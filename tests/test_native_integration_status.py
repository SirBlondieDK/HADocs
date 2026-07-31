from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from hadocs.application.hask_candidate_evidence import (
    CandidateClassification,
)
from hadocs.application.operational_database import (
    OperationalDatabaseOperation,
    persist_operational_database,
)
from hadocs.collectors.installation import InstallationCollector
from hadocs.collectors.native_integration_status import (
    CONTRACT_VERSION,
    NativeIntegrationStatusCollector,
    NativeIntegrationStatusError,
)
from hadocs.core.models import EntityModel, InstallationModel
from hadocs.hask_database import (
    CredentialStoreSecretProvider,
    IdempotencyConflictError,
    schema_sha256,
)
from hadocs.knowledge.hask_pilot.loader import REQUIRED


OBSERVED_AT = "2026-07-28T04:00:00Z"
SCOPE = "is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194"
HANDLE = f"HADocs/DatabaseIdentity/{SCOPE}/1"
SECRET = bytes(range(32))
SCHEMA_HASH = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"


class StubProvider:
    def __init__(self, entries: list[dict[str, object]] | None = None) -> None:
        self.entries = entries or []
        self.config_entry_calls = 0

    def get_states(self): return []
    def get_config(self): return {}
    def get_services(self): return []
    def get_entities(self): return []
    def get_devices(self): return []
    def get_areas(self): return []
    def get_labels(self): return []

    def get_config_entries(self):
        self.config_entry_calls += 1
        return deepcopy(self.entries)


class MemoryBackend:
    backend_kind = "windows_credential_manager"

    def __init__(self) -> None:
        self.values = {HANDLE: SECRET}

    def write(self, handle: str, value: bytes) -> None:
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


def secret_provider(backend: MemoryBackend) -> CredentialStoreSecretProvider:
    return CredentialStoreSecretProvider(backend)


def entry(
    entry_id: str,
    domain: str,
    state: str,
    **extra: object,
) -> dict[str, object]:
    return {
        "entry_id": entry_id,
        "domain": domain,
        "state": state,
        "title": f"PRIVATE TITLE {entry_id}",
        "unique_id": f"PRIVATE UNIQUE {entry_id}",
        "options": {"host": "192.0.2.8"},
        "reason": f"PRIVATE ERROR {entry_id}",
        **extra,
    }


def collect(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    return NativeIntegrationStatusCollector(clock=lambda: OBSERVED_AT).collect(
        StubProvider(entries)
    )


def _typed_matcher(matcher_id: str, platform: str, target: str) -> dict[str, object]:
    return {
        "id": matcher_id,
        "matcher_contract": {
            "version": "1.0.0",
            "platform_scope": {"include": [platform]},
            "observation_types": ["connectivity_result"],
            "required_fields": [
                {"path": "connection_result", "value_type": "string"},
                {"path": "problem_signal", "value_type": "boolean"},
            ],
            "evidence_target": target,
            "outcomes": {
                "conflict": "preserve_conflict",
                "match": "canonical_evidence",
                "missing_evidence": "preserve_missing_evidence",
                "no_match": "preserve_no_match",
                "partial_match": "preserve_partial",
                "unknown_applicability": "preserve_unknown_applicability",
            },
        },
    }


def synthetic_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "native-status-bundle"
    bundle.mkdir()
    artifacts: dict[str, dict[str, object]] = {
        name: {
            "artifact_kind": name.removesuffix(".json"),
            "contract_version": "1.1.0",
            "items": [],
        }
        for name in REQUIRED
    }
    artifacts["evidence_matchers.json"]["items"] = [
        _typed_matcher(
            "unifi_controller_connectivity_failure",
            "unifi",
            "unifi_controller_connection_state",
        ),
        _typed_matcher(
            "mikrotik_api_connectivity_failure",
            "mikrotik",
            "mikrotik_api_connection_state",
        ),
    ]
    artifacts["platform_index.json"]["items"] = [
        {"id": "unifi"},
        {"id": "mikrotik"},
    ]
    hashes: dict[str, str] = {}
    aggregate = hashlib.sha256()
    for name in sorted(REQUIRED):
        target = bundle / name
        target.write_text(
            json.dumps(artifacts[name], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        aggregate.update(name.encode())
        aggregate.update(b"\0")
        aggregate.update(target.read_bytes())
        aggregate.update(b"\0")
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "contract_name": "hask-hadocs",
                "contract_version": "1.1.0",
                "knowledge_content_version": "synthetic-1",
                "knowledge_schema_version": "1.0.0",
                "authoritative_sha256": "0" * 64,
                "schema_registry_sha256": "1" * 64,
                "artifact_sha256": aggregate.hexdigest(),
                "artifacts": hashes,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle


def bundle_hashes(bundle: Path) -> dict[str, str]:
    return {
        item.name: hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(bundle.iterdir())
        if item.is_file()
    }


def model(platform: str, observations: list[dict[str, object]] | None) -> InstallationModel:
    raw_id = f"sensor.private_{platform}"
    raw: dict[str, object] = {
        "findings": ["PRIVATE FINDING"],
        "recommendations": ["PRIVATE RECOMMENDATION"],
        "health_score": 71,
    }
    if observations is not None:
        raw["native_integration_status"] = deepcopy(observations)
    entity = EntityModel(
        entity_id=raw_id,
        name="PRIVATE ENTITY NAME",
        domain="sensor",
        platform=platform,
        state="PRIVATE ENTITY STATE",
        area_id=None,
        device_id=None,
        is_ignored=False,
        is_physical=True,
        attributes={"token": "PRIVATE TOKEN"},
        registry={"entity_id": raw_id, "platform": platform, "labels": []},
    )
    return InstallationModel(
        areas={},
        devices={},
        entities={raw_id: entity},
        integrations={},
        config={},
        states=[],
        services=[],
        labels=[],
        raw=raw,
    )


def app_config(path: Path, bundle: Path) -> dict[str, object]:
    return {
        "hask_database_enabled": True,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "native-status-tests",
        "hask_database_identity_version": 1,
        "hask_database_installation_uuid": "123e4567-e89b-42d3-a456-426614174000",
        "hask_database_installation_scope": SCOPE,
        "hask_database_secret_handle": HANDLE,
        "hask_database_secret_generation": 1,
        "hask_database_identity_state": "initialized",
        "hask_database_secret_backend": "windows_credential_manager",
        "hask_enabled": True,
        "hask_candidate_evidence_enabled": True,
        "hask_native_integration_status_enabled": True,
        "hask_bundle_path": str(bundle),
    }


def operation(identity: str = "native-status-operation") -> OperationalDatabaseOperation:
    return OperationalDatabaseOperation(identity, OBSERVED_AT, "2026-07-28T04:00:01Z")


def persist(
    tmp_path: Path,
    platform: str,
    observations: list[dict[str, object]] | None,
    *,
    identity: str = "native-status-operation",
    path: Path | None = None,
    bundle: Path | None = None,
    backend: MemoryBackend | None = None,
):
    selected_bundle = bundle or synthetic_bundle(tmp_path)
    selected_path = path or tmp_path / "native-status.sqlite"
    selected_backend = backend or MemoryBackend()
    installation = model(platform, observations)
    result = persist_operational_database(
        installation,
        app_config(selected_path, selected_bundle),
        operation=operation(identity),
        secret_provider=secret_provider(selected_backend),
    )
    return result, installation, selected_path, selected_bundle, selected_backend


def candidate(result, matcher: str):
    assert result.hask_candidate_evidence is not None
    return next(
        item for item in result.hask_candidate_evidence.candidates
        if item.matcher_id == matcher
    )


def database_counts(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        return {
            table: connection.execute(
                f'SELECT count(*) FROM "{table}"'
            ).fetchone()[0]
            for table in tables
        }
    finally:
        connection.close()


def test_disabled_feature_preserves_collection_and_issues_no_request():
    provider = StubProvider([entry("PRIVATE-ID", "unifi", "setup_retry")])
    data = InstallationCollector(
        provider=provider,
        config={"save_raw_cache": False},
        log=lambda _: None,
    ).collect()
    assert provider.config_entry_calls == 0
    assert "native_integration_status" not in data
    assert set(data) == {"states", "config", "services", "entities", "devices", "areas", "labels"}


def test_enabled_collection_issues_exactly_one_request_and_emits_aggregates(tmp_path):
    provider = StubProvider([entry("PRIVATE-ID", "unifi", "setup_retry")])
    data = InstallationCollector(
        provider=provider,
        config=app_config(tmp_path / "collector.sqlite", tmp_path),
        log=lambda _: None,
    ).collect()
    assert provider.config_entry_calls == 1
    assert len(data["native_integration_status"]) == 1


def test_enabled_native_flag_without_initialized_database_issues_no_request():
    provider = StubProvider([entry("PRIVATE-ID", "unifi", "setup_retry")])
    data = InstallationCollector(
        provider=provider,
        config={
            "save_raw_cache": False,
            "hask_native_integration_status_enabled": True,
            "hask_database_enabled": False,
        },
        log=lambda _: None,
    ).collect()
    assert provider.config_entry_calls == 0
    assert "native_integration_status" not in data


def test_aggregation_discards_identity_and_prohibited_fields():
    observations = collect([
        entry("PRIVATE-ID-A", "unifi", "setup_retry", future={"secret": "x"}),
        entry("PRIVATE-ID-B", "unifi", "loaded"),
    ])
    encoded = json.dumps(observations, sort_keys=True)
    assert "PRIVATE" not in encoded
    assert "192.0.2.8" not in encoded
    assert set(observations[0]) == {
        "contract_version", "domain", "entry_count", "state_counts",
        "problem_entry_count", "unknown_state_count", "observed_at",
        "evidence_quality", "immutable_digest",
    }
    assert observations[0]["entry_count"] == 2
    assert observations[0]["state_counts"] == {"loaded": 1, "setup_retry": 1}


def test_input_order_does_not_change_output_or_digest():
    values = [entry("A", "unifi", "loaded"), entry("B", "unifi", "setup_retry")]
    assert collect(values) == collect(list(reversed(values)))


def test_duplicate_response_identity_is_counted_once_and_never_emitted():
    duplicate = entry("PRIVATE-DUPLICATE", "unifi", "setup_retry")
    observations = collect([duplicate, deepcopy(duplicate)])
    assert observations[0]["entry_count"] == 1
    assert "PRIVATE-DUPLICATE" not in repr(observations)


def test_conflicting_duplicate_fails_with_redacted_error():
    with pytest.raises(NativeIntegrationStatusError) as caught:
        collect([
            entry("PRIVATE-CONFLICT", "unifi", "loaded"),
            entry("PRIVATE-CONFLICT", "unifi", "setup_retry"),
        ])
    assert "PRIVATE-CONFLICT" not in str(caught.value)


def test_unknown_state_increments_only_unknown_count_and_is_not_emitted():
    observations = collect([entry("A", "unifi", "FUTURE_PRIVATE_STATE")])
    assert observations[0]["unknown_state_count"] == 1
    assert observations[0]["state_counts"] == {}
    assert observations[0]["problem_entry_count"] == 0
    assert "FUTURE_PRIVATE_STATE" not in repr(observations)


@pytest.mark.parametrize(
    "state",
    ("setup_error", "migration_error", "setup_retry", "failed_unload"),
)
def test_only_verified_problem_states_increment_problem_count(state):
    assert collect([entry("A", "unifi", state)])[0]["problem_entry_count"] == 1


def test_unrelated_domains_are_not_emitted_or_used_as_display_names():
    assert collect([entry("A", "mqtt", "setup_retry")]) == []
    with pytest.raises(NativeIntegrationStatusError):
        collect([entry("A", "UniFi Network", "setup_retry")])


def test_persistence_replay_is_restart_safe_and_creates_no_duplicate(tmp_path):
    observations = collect([entry("PRIVATE-ID", "unifi", "setup_retry")])
    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "replay.sqlite"
    backend = MemoryBackend()
    first, _, _, _, _ = persist(
        tmp_path, "unifi", observations, path=path, bundle=bundle, backend=backend
    )
    counts = database_counts(path)
    second, _, _, _, _ = persist(
        tmp_path, "unifi", observations, path=path, bundle=bundle, backend=backend
    )
    assert second.observation_ids == first.observation_ids
    assert second.scan_run_id == first.scan_run_id
    assert database_counts(path) == counts


def test_changed_aggregate_under_same_operation_conflicts_without_writes(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "conflict.sqlite"
    backend = MemoryBackend()
    first = collect([entry("PRIVATE-ID", "unifi", "setup_retry")])
    changed = collect([entry("PRIVATE-ID", "unifi", "loaded")])
    persist(tmp_path, "unifi", first, path=path, bundle=bundle, backend=backend)
    counts = database_counts(path)
    with pytest.raises(IdempotencyConflictError):
        persist(tmp_path, "unifi", changed, path=path, bundle=bundle, backend=backend)
    assert database_counts(path) == counts


def test_problem_state_satisfies_only_problem_signal_for_unifi(tmp_path):
    result, _, _, _, _ = persist(
        tmp_path, "unifi", collect([entry("A", "unifi", "setup_retry")])
    )
    item = candidate(result, "unifi_controller_connectivity_failure")
    assert item.classification is CandidateClassification.INSUFFICIENT_EVIDENCE
    assert item.missing_evidence_categories == ("NATIVE_CONNECTION_RESULT",)


def test_loaded_state_does_not_prove_connectivity(tmp_path):
    result, _, _, _, _ = persist(
        tmp_path, "unifi", collect([entry("A", "unifi", "loaded")])
    )
    item = candidate(result, "unifi_controller_connectivity_failure")
    assert item.classification is CandidateClassification.INSUFFICIENT_EVIDENCE
    assert item.missing_evidence_categories == ("NATIVE_CONNECTION_RESULT",)
    assert item.classification is not CandidateClassification.SUPPORTED_CANDIDATE


def test_mikrotik_problem_state_remains_insufficient(tmp_path):
    result, _, _, _, _ = persist(
        tmp_path, "mikrotik", collect([entry("A", "mikrotik", "setup_error")])
    )
    item = candidate(result, "mikrotik_api_connectivity_failure")
    assert item.classification is CandidateClassification.INSUFFICIENT_EVIDENCE
    assert item.missing_evidence_categories == ("NATIVE_CONNECTION_RESULT",)


def test_missing_platform_is_not_applicable(tmp_path):
    result, _, _, _, _ = persist(
        tmp_path, "mqtt", collect([entry("A", "unifi", "setup_retry")])
    )
    assert {
        item.classification for item in result.hask_candidate_evidence.candidates
    } == {CandidateClassification.NOT_APPLICABLE}


def test_mixed_domain_states_are_rejected_as_conflict(tmp_path):
    observations = collect([
        entry("A", "unifi", "setup_retry"),
        entry("B", "unifi", "loaded"),
    ])
    result, _, _, _, _ = persist(tmp_path, "unifi", observations)
    item = candidate(result, "unifi_controller_connectivity_failure")
    assert item.classification is CandidateClassification.REJECTED_CONFLICT
    assert item.rejection_code == "CONTRADICTORY_DOMAIN_STATUS_EVIDENCE"


def test_multiple_problem_entries_remain_ambiguous(tmp_path):
    observations = collect([
        entry("A", "unifi", "setup_retry"),
        entry("B", "unifi", "setup_retry"),
    ])
    result, _, _, _, _ = persist(tmp_path, "unifi", observations)
    item = candidate(result, "unifi_controller_connectivity_failure")
    assert item.classification is CandidateClassification.INSUFFICIENT_EVIDENCE
    assert item.missing_evidence_categories == (
        "NATIVE_CONNECTION_RESULT", "NATIVE_PROBLEM_SIGNAL"
    )


def test_unknown_state_remains_insufficient(tmp_path):
    result, _, _, _, _ = persist(
        tmp_path, "unifi", collect([entry("A", "unifi", "future_state")])
    )
    item = candidate(result, "unifi_controller_connectivity_failure")
    assert item.missing_evidence_categories == (
        "NATIVE_CONNECTION_RESULT", "NATIVE_PROBLEM_SIGNAL"
    )


def test_old_domain_status_is_not_carried_into_a_new_scan(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "freshness.sqlite"
    backend = MemoryBackend()
    persist(
        tmp_path,
        "unifi",
        collect([entry("A", "unifi", "setup_retry")]),
        identity="first",
        path=path,
        bundle=bundle,
        backend=backend,
    )
    current, _, _, _, _ = persist(
        tmp_path,
        "unifi",
        None,
        identity="second",
        path=path,
        bundle=bundle,
        backend=backend,
    )
    item = candidate(current, "unifi_controller_connectivity_failure")
    assert item.missing_evidence_categories == (
        "NATIVE_CONNECTION_RESULT", "NATIVE_PROBLEM_SIGNAL"
    )


def test_sqlite_results_errors_and_bundle_are_private_and_analytics_unchanged(tmp_path):
    raw_id = "PRIVATE-CONFIG-ENTRY-ID"
    observations = collect([entry(raw_id, "unifi", "setup_retry")])
    bundle = synthetic_bundle(tmp_path)
    before_bundle = bundle_hashes(bundle)
    installation = model("unifi", observations)
    before_model = deepcopy(installation)
    path = tmp_path / "privacy.sqlite"
    result = persist_operational_database(
        installation,
        app_config(path, bundle),
        operation=operation(),
        secret_provider=secret_provider(MemoryBackend()),
    )
    public = repr(result).encode() + result.hask_candidate_evidence.canonical_bytes()
    assert raw_id.encode() not in public
    assert raw_id.encode() not in path.read_bytes()
    assert b"PRIVATE TITLE" not in path.read_bytes()
    assert b"192.0.2.8" not in path.read_bytes()
    assert installation == before_model
    assert bundle_hashes(bundle) == before_bundle


def test_schema_integrity_and_domain_payload_are_exact(tmp_path):
    result, _, path, _, _ = persist(
        tmp_path, "unifi", collect([entry("PRIVATE-ID", "unifi", "setup_retry")])
    )
    connection = sqlite3.connect(path)
    try:
        rows = connection.execute(
            "SELECT observation_key,normalized_payload_json FROM observation "
            "WHERE observation_key LIKE ?",
            (f"{CONTRACT_VERSION}:%",),
        ).fetchall()
        assert len(rows) == 1
        payload = json.loads(rows[0][1])
        assert payload["domain"] == "unifi"
        assert payload["entry_count"] == 1
        assert len(result.observation_ids) == 2
        assert schema_sha256(connection) == SCHEMA_HASH
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    finally:
        connection.close()
