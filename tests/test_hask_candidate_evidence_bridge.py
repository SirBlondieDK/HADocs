from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from hadocs.application.hask_candidate_evidence import (
    CandidateBridgeState,
    CandidateClassification,
    MatcherReadinessState,
    build_candidate_evidence_bridge,
)
from hadocs.application.operational_database import (
    OperationalDatabaseOperation,
    persist_operational_database,
)
from hadocs.core.models import EntityModel, InstallationModel
from hadocs.hask_database import (
    CapabilityOutcomeInput,
    CredentialStoreSecretProvider,
    EntityPersistenceInput,
    EntityPersistenceRequest,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    ObservationInput,
    OperationalSliceRequest,
    RelationshipPersistenceInput,
    RelationshipPersistenceRequest,
    ScanCompletionIntent,
)
from hadocs.knowledge.hask_pilot.loader import REQUIRED
from hadocs.knowledge.hask_runtime import BundleManager


SCOPE = "is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194"
HANDLE = f"HADocs/DatabaseIdentity/{SCOPE}/1"
SECRET = bytes(range(32))
SCHEMA_HASH = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"


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


def provider(backend: MemoryBackend) -> CredentialStoreSecretProvider:
    return CredentialStoreSecretProvider(backend)


def _typed_matcher(
    matcher_id: str, platform: str, evidence_target: str
) -> dict[str, object]:
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
            "evidence_target": evidence_target,
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
    bundle = tmp_path / "synthetic-hask-bundle"
    bundle.mkdir()
    artifacts: dict[str, dict[str, object]] = {
        name: {"artifact_kind": name.removesuffix(".json"), "contract_version": "1.1.0", "items": []}
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
    artifact_hashes: dict[str, str] = {}
    for name in sorted(REQUIRED):
        target = bundle / name
        target.write_text(
            json.dumps(artifacts[name], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifact_hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    aggregate = hashlib.sha256()
    for name in sorted(REQUIRED):
        aggregate.update(name.encode())
        aggregate.update(b"\0")
        aggregate.update((bundle / name).read_bytes())
        aggregate.update(b"\0")
    manifest = {
        "contract_name": "hask-hadocs",
        "contract_version": "1.1.0",
        "knowledge_content_version": "synthetic-1",
        "knowledge_schema_version": "1.0.0",
        "authoritative_sha256": "0" * 64,
        "schema_registry_sha256": "1" * 64,
        "artifact_sha256": aggregate.hexdigest(),
        "artifacts": artifact_hashes,
    }
    (bundle / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return bundle


def bundle_hashes(bundle: Path) -> dict[str, str]:
    return {
        item.name: hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(bundle.iterdir())
        if item.is_file()
    }


def model(*platforms: str, reverse: bool = False) -> InstallationModel:
    values = list(enumerate(platforms))
    if reverse:
        values.reverse()
    entities: dict[str, EntityModel] = {}
    for ordinal, platform in values:
        raw_id = f"sensor.private_{ordinal}_{platform}"
        entities[raw_id] = EntityModel(
            entity_id=raw_id,
            name=f"PROHIBITED NAME {ordinal}",
            domain="sensor",
            platform=platform,
            state="PROHIBITED STATE",
            area_id=None,
            device_id=None,
            is_ignored=False,
            is_physical=True,
            attributes={"token": "PROHIBITED TOKEN"},
            registry={"entity_id": raw_id, "platform": platform, "labels": []},
        )
    return InstallationModel(
        areas={},
        devices={},
        entities=entities,
        integrations={},
        config={"url": "https://192.0.2.1", "token": "PROHIBITED TOKEN"},
        states=[],
        services=[],
        labels=[],
        raw={
            "findings": ["PROHIBITED FINDING"],
            "recommendations": ["PROHIBITED RECOMMENDATION"],
            "health_score": 73,
        },
    )


def app_config(
    path: Path,
    bundle: Path,
    *,
    database_enabled: bool = True,
    hask_enabled: bool = True,
    bridge_enabled: bool = True,
) -> dict[str, object]:
    return {
        "hask_database_enabled": database_enabled,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "candidate-bridge-tests",
        "hask_database_identity_version": 1,
        "hask_database_installation_uuid": "123e4567-e89b-42d3-a456-426614174000",
        "hask_database_installation_scope": SCOPE,
        "hask_database_secret_handle": HANDLE,
        "hask_database_secret_generation": 1,
        "hask_database_identity_state": "initialized",
        "hask_database_secret_backend": "windows_credential_manager",
        "hask_enabled": hask_enabled,
        "hask_candidate_evidence_enabled": bridge_enabled,
        "hask_bundle_path": str(bundle),
    }


def operation() -> OperationalDatabaseOperation:
    return OperationalDatabaseOperation(
        "candidate-evidence-operation",
        "2026-07-28T02:00:00Z",
        "2026-07-28T02:00:01Z",
    )


def database_counts(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        tables = tuple(
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        return {
            table: connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in tables
        }
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("database_enabled", "hask_enabled", "bridge_enabled"),
    ((False, False, False), (True, False, False), (False, True, True)),
)
def test_feature_combinations_do_not_cross_activate(
    tmp_path, monkeypatch, database_enabled, hask_enabled, bridge_enabled
):
    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "feature-gates.sqlite"

    def forbidden(*args, **kwargs):
        raise AssertionError("HASK bundle activity was not authorized")

    monkeypatch.setattr(BundleManager, "startup", forbidden)
    result = persist_operational_database(
        model("unifi"),
        app_config(
            path,
            bundle,
            database_enabled=database_enabled,
            hask_enabled=hask_enabled,
            bridge_enabled=bridge_enabled,
        ),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    assert result.hask_candidate_evidence is None
    assert path.exists() is database_enabled


def test_invalid_bundle_fails_closed_without_analytical_changes(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    target = bundle / "evidence_matchers.json"
    target.write_bytes(target.read_bytes() + b" ")
    before_bundle = bundle_hashes(bundle)
    installation = model("unifi")
    before_model = deepcopy(installation)
    result = persist_operational_database(
        installation,
        app_config(tmp_path / "invalid.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    bridge = result.hask_candidate_evidence
    assert bridge is not None
    assert bridge.state is CandidateBridgeState.REJECTED
    assert bridge.rejection_code == "BUNDLE_VALIDATION_FAILED"
    assert bridge.candidates == ()
    assert installation == before_model
    assert bundle_hashes(bundle) == before_bundle


def test_platform_absence_is_not_applicable(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    result = persist_operational_database(
        model("mqtt"),
        app_config(tmp_path / "not-applicable.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    bridge = result.hask_candidate_evidence
    assert bridge is not None and bridge.state is CandidateBridgeState.READY
    assert {item.classification for item in bridge.candidates} == {
        CandidateClassification.NOT_APPLICABLE
    }


def test_unifi_and_mikrotik_presence_preserve_missing_native_evidence(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    result = persist_operational_database(
        model("unifi", "mikrotik"),
        app_config(tmp_path / "missing-evidence.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    bridge = result.hask_candidate_evidence
    assert bridge is not None
    insufficient = tuple(
        item for item in bridge.candidates
        if item.classification is CandidateClassification.INSUFFICIENT_EVIDENCE
    )
    assert {item.matcher_id for item in insufficient} == {
        "unifi_controller_connectivity_failure",
        "mikrotik_api_connectivity_failure",
    }
    assert all(item.missing_evidence_categories == (
        "NATIVE_CONNECTION_RESULT", "NATIVE_PROBLEM_SIGNAL"
    ) for item in insufficient)
    assert all(item.supporting_relationship_ids for item in insufficient)
    assert all(item.supporting_observation_ids for item in insufficient)
    assert all(item.consumer_contract_version == "1.1.0" for item in insufficient)
    assert not any(
        item.classification is CandidateClassification.SUPPORTED_CANDIDATE
        for item in bridge.candidates
    )


def _conflicting_persisted_scan(path: Path):
    backend = MemoryBackend()
    service = HaskDatabaseService(
        HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path)),
        provider(backend),
    )
    service.startup()
    start = service.persist_operational_slice(OperationalSliceRequest(
        recovery_set_ref="candidate-conflict",
        installation_scope=SCOPE,
        secret_handle=HANDLE,
        secret_generation=1,
        context_format_version=1,
        scan_idempotency_key="candidate-conflict-scan",
        started_at="2026-07-28T03:00:00Z",
        implementation_version="candidate-bridge-tests",
        contract_version="candidate-bridge-tests",
        observations=(ObservationInput(
            observation_key="hadocs.normalized-counts.v1",
            taxonomy_class="B",
            authority_class="STRUCTURED_CONTEXT_DEPENDENT",
            observed_at="2026-07-28T03:00:00Z",
            payload={"areas": 0, "devices": 0, "entities": 1, "integrations": 2},
            privacy_class="LOCAL_ONLY",
            retention_policy="RETAIN_UNTIL_SUPERSEDED",
        ),),
    ))
    entity = service.persist_entities(EntityPersistenceRequest(
        installation_id=start.installation_id,
        context_id=start.context_id,
        scan_run_id=start.scan_run_id,
        observation_id=start.observation_ids[0],
        event_at="2026-07-28T03:00:00Z",
        entities=(EntityPersistenceInput("conflict-entity", "sensor.private_conflict"),),
    ))
    service.persist_relationships(RelationshipPersistenceRequest(
        installation_id=start.installation_id,
        context_id=start.context_id,
        scan_run_id=start.scan_run_id,
        observation_id=start.observation_ids[0],
        event_at="2026-07-28T03:00:00Z",
        relationships=(
            RelationshipPersistenceInput(
                "conflict-unifi", "sensor.private_conflict",
                "entity_uses_platform", "integration", "unifi",
            ),
            RelationshipPersistenceInput(
                "conflict-mikrotik", "sensor.private_conflict",
                "entity_uses_platform", "integration", "mikrotik",
            ),
        ),
    ))
    completion = service.complete_scan(ScanCompletionIntent(
        completion_idempotency_key="candidate-conflict-completion",
        terminal_at="2026-07-28T03:00:01Z",
        terminal_status="SUCCEEDED",
        completeness="COMPLETE",
        safe_error_code=None,
        capabilities=(CapabilityOutcomeInput(
            capability_id="hadocs.normalized-counts.v1",
            status="SUCCEEDED",
            retryable=None,
            safe_error_code=None,
            observation_contribution=True,
            completeness_contribution="COMPLETE",
        ),),
    ).bind(start))
    assert entity.entities
    return service, start, completion


def test_contradictory_current_platform_evidence_is_rejected_without_writes(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "conflict.sqlite"
    service, start, completion = _conflicting_persisted_scan(path)
    before = database_counts(path)
    result = build_candidate_evidence_bridge(
        service=service,
        operational_slice=start,
        completion=completion,
        config=app_config(path, bundle),
    )
    after = database_counts(path)
    service.shutdown()
    assert result.state is CandidateBridgeState.READY
    assert result.candidates
    assert {item.classification for item in result.candidates} == {
        CandidateClassification.REJECTED_CONFLICT
    }
    assert {item.rejection_code for item in result.candidates} == {
        "CONTRADICTORY_CURRENT_PLATFORM_EVIDENCE"
    }
    assert after == before


def test_replay_is_byte_identical_read_only_and_bundle_is_immutable(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    bundle_before = bundle_hashes(bundle)
    path = tmp_path / "replay.sqlite"
    backend = MemoryBackend()
    first = persist_operational_database(
        model("unifi", "mikrotik"),
        app_config(path, bundle),
        operation=operation(),
        secret_provider=provider(backend),
    )
    counts = database_counts(path)
    replay = persist_operational_database(
        model("unifi", "mikrotik"),
        app_config(path, bundle),
        operation=operation(),
        secret_provider=provider(backend),
    )
    assert first.hask_candidate_evidence is not None
    assert replay.hask_candidate_evidence is not None
    assert first.hask_candidate_evidence.canonical_bytes() == (
        replay.hask_candidate_evidence.canonical_bytes()
    )
    assert database_counts(path) == counts
    assert bundle_hashes(bundle) == bundle_before


def test_input_order_does_not_change_candidate_order_or_digest(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    first = persist_operational_database(
        model("unifi", "mikrotik"),
        app_config(tmp_path / "ordered-a.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    second = persist_operational_database(
        model("unifi", "mikrotik", reverse=True),
        app_config(tmp_path / "ordered-b.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    assert first.hask_candidate_evidence is not None
    assert second.hask_candidate_evidence is not None
    assert first.hask_candidate_evidence.canonical_bytes() == (
        second.hask_candidate_evidence.canonical_bytes()
    )


def test_candidate_output_is_redacted_and_has_no_analytical_side_effect(tmp_path):
    bundle = synthetic_bundle(tmp_path)
    installation = model("unifi")
    before = deepcopy(installation)
    result = persist_operational_database(
        installation,
        app_config(tmp_path / "privacy.sqlite", bundle),
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    bridge = result.hask_candidate_evidence
    assert bridge is not None
    public = bridge.canonical_bytes() + repr(bridge).encode()
    for prohibited in (
        "sensor.private_0_unifi",
        "PROHIBITED NAME",
        "PROHIBITED STATE",
        "PROHIBITED TOKEN",
        "PROHIBITED FINDING",
        "PROHIBITED RECOMMENDATION",
        "192.0.2.1",
    ):
        assert prohibited.encode() not in public
    assert installation == before
    assert installation.raw["findings"] == ["PROHIBITED FINDING"]
    assert installation.raw["recommendations"] == ["PROHIBITED RECOMMENDATION"]
    assert installation.raw["health_score"] == 73
    assert all(item.candidate_digest.startswith("hce1_") for item in bridge.candidates)


def test_schema_is_unchanged_after_bridge_execution(tmp_path):
    from hadocs.hask_database import schema_sha256

    bundle = synthetic_bundle(tmp_path)
    path = tmp_path / "schema.sqlite"
    persist_operational_database(
        model("unifi"), app_config(path, bundle), operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )
    connection = sqlite3.connect(path)
    try:
        assert schema_sha256(connection) == SCHEMA_HASH
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    finally:
        connection.close()


def test_packaged_bundle_is_used_when_explicit_path_is_absent(tmp_path):
    configured = app_config(
        tmp_path / "packaged-bundle.sqlite",
        synthetic_bundle(tmp_path),
    )
    configured.pop("hask_bundle_path")

    result = persist_operational_database(
        model("unifi"),
        configured,
        operation=operation(),
        secret_provider=provider(MemoryBackend()),
    )

    bridge = result.hask_candidate_evidence
    assert bridge is not None
    assert bridge.state is CandidateBridgeState.READY
    assert bridge.rejection_code is None
    assert bridge.candidates
    assert {item.matcher_id for item in bridge.candidates}

    assert len(bridge.matcher_readiness) == 3
    readiness = {
        item.matcher_id: item for item in bridge.matcher_readiness
    }
    assert set(readiness) == {
        "unifi_controller_connectivity_failure",
        "mikrotik_api_connectivity_failure",
        "tuya_integration_status_problem",
    }
    assert (
        readiness["unifi_controller_connectivity_failure"].state
        is MatcherReadinessState.BLOCKED
    )
    assert (
        readiness["mikrotik_api_connectivity_failure"].state
        is MatcherReadinessState.NOT_APPLICABLE
    )
    assert (
        readiness["tuya_integration_status_problem"].state
        is MatcherReadinessState.NOT_APPLICABLE
    )
