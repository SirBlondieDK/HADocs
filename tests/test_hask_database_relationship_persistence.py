from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import struct
import unicodedata

import pytest

from hadocs.application.operational_database import (
    OperationalDatabaseOperation,
    persist_operational_database,
)
from hadocs.core.models import EntityModel, InstallationModel
from hadocs.hask_database import (
    CredentialStoreSecretProvider,
    EntityPersistenceInput,
    EntityPersistenceRequest,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    IdempotencyConflictError,
    NotFoundError,
    ObservationInput,
    OperationalSliceRequest,
    RELATIONSHIP_RECREATION_REASON,
    RELATIONSHIP_REMOVAL_REASON,
    RelationshipPersistenceInput,
    RelationshipPersistenceRequest,
    ValidationFailureError,
    schema_sha256,
)


SCHEMA_HASH = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"
SCOPE = "is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194"
SECRET = bytes(range(32))
HANDLE = f"HADocs/DatabaseIdentity/{SCOPE}/1"
SOURCE_RAW = "sensor.kitchen_temperature"
CA_DOMAIN = b"HASK/HADOCS/OPAQUE-REFERENCE/HMAC-SHA-256"


class FixedProvider:
    def __init__(self, secret: bytes = SECRET) -> None:
        self.secret = secret
        self.loads = 0

    def load(self, handle: str, generation: int) -> bytes:
        self.loads += 1
        assert handle == HANDLE
        assert generation == 1
        return self.secret


class MemoryBackend:
    def __init__(self, secret: bytes, backend_kind: str) -> None:
        self.backend_kind = backend_kind
        self.values = {HANDLE: secret}

    def write(self, handle: str, value: bytes) -> None:
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


def factory(path):
    return HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))


def start_request(
    *,
    scan_key: str = "relationship-scan-1",
    started_at: str = "2026-07-27T20:00:00Z",
    recovery_set_ref: str = "recovery:relationship-tests",
) -> OperationalSliceRequest:
    return OperationalSliceRequest(
        recovery_set_ref=recovery_set_ref,
        installation_scope=SCOPE,
        secret_handle=HANDLE,
        secret_generation=1,
        context_format_version=1,
        scan_idempotency_key=scan_key,
        started_at=started_at,
        implementation_version="relationship-batch-4b",
        contract_version="relationship-persistence-v1",
        observations=(ObservationInput(
            observation_key="normalized-counts",
            taxonomy_class="B",
            authority_class="STRUCTURED_CONTEXT_DEPENDENT",
            observed_at=started_at,
            payload={"entities": 1, "relationships": 1},
            privacy_class="LOCAL_ONLY",
            retention_policy="RETAIN_UNTIL_SUPERSEDED",
        ),),
    )


def prepare_scan(
    service: HaskDatabaseService,
    *,
    scan_key: str = "relationship-scan-1",
    started_at: str = "2026-07-27T20:00:00Z",
    recovery_set_ref: str = "recovery:relationship-tests",
    source_raw: str = SOURCE_RAW,
):
    start = service.persist_operational_slice(start_request(
        scan_key=scan_key,
        started_at=started_at,
        recovery_set_ref=recovery_set_ref,
    ))
    entity = service.persist_entities(EntityPersistenceRequest(
        installation_id=start.installation_id,
        context_id=start.context_id,
        scan_run_id=start.scan_run_id,
        observation_id=start.observation_ids[0],
        event_at=started_at,
        entities=(EntityPersistenceInput("source-entity", source_raw),),
    ))
    return start, entity


def relationship_request(start, *items, event_at: str = "2026-07-27T20:00:00Z"):
    return RelationshipPersistenceRequest(
        installation_id=start.installation_id,
        context_id=start.context_id,
        scan_run_id=start.scan_run_id,
        observation_id=start.observation_ids[0],
        event_at=event_at,
        relationships=tuple(items),
    )


def relationship_input(
    *,
    key: str = "relationship-000000",
    predicate: str = "entity_assigned_to_device",
    target_kind: str = "device",
    target_raw: str = "device-\N{GREEK SMALL LETTER ALPHA}",
    source_raw: str = SOURCE_RAW,
    current_status: str = "CURRENT",
    reason_code: str = "RELATIONSHIP_PRESENT_VALID",
    expected_target_ref: str | None = None,
) -> RelationshipPersistenceInput:
    return RelationshipPersistenceInput(
        relationship_key=key,
        raw_source_entity_id=source_raw,
        predicate=predicate,
        target_kind=target_kind,
        raw_target_id=target_raw,
        current_status=current_status,
        reason_code=reason_code,
        expected_target_ref=expected_target_ref,
    )


def table_counts(path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "identity_registration",
                "relationship",
                "relationship_current_state",
                "relationship_lifecycle_event",
                "audit_record",
                "audit_subject_link",
                "audit_evidence_link",
            )
        }
    finally:
        connection.close()


def frame(value: str) -> bytes:
    encoded = unicodedata.normalize("NFC", value).encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def ca001_reference(
    kind: str, raw_identifier: str, scope: str = SCOPE
) -> str:
    payload = (
        CA_DOMAIN
        + struct.pack(">I", 1)
        + struct.pack(">I", 3)
        + frame(kind)
        + frame(scope)
        + frame(raw_identifier)
    )
    return f"refh1_{kind}_{hmac.new(SECRET, payload, hashlib.sha256).hexdigest()}"


def loaded_component_reference(component: str) -> str:
    normalized = unicodedata.normalize("NFC", component).encode("utf-8")
    allowed = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    escaped = "".join(
        chr(byte) if byte in allowed else f"%{byte:02X}" for byte in normalized
    )
    canonical_key = f"ck1:loaded_component:{escaped}"
    payload = (
        frame("hadocs-generic-metadata/observation-id/v1")
        + frame(SCOPE)
        + frame("rest.components")
        + frame(canonical_key)
    )
    return f"obs1_{hashlib.sha256(payload).hexdigest()}"


def relationship_reference(predicate: str, source_ref: str, target_ref: str) -> str:
    payload = (
        frame("hadocs-generic-metadata/relationship-id/v1")
        + frame(SCOPE)
        + frame(predicate)
        + frame(source_ref)
        + frame(target_ref)
    )
    return f"rel1_{hashlib.sha256(payload).hexdigest()}"


@pytest.mark.parametrize(
    ("predicate", "target_kind", "target_raw", "expected_target"),
    (
        (
            "entity_uses_platform",
            "integration",
            "mqtt",
            "obs1_79927229da53e5b9d0b9b2e503f769329d20e7a475285cb24553ee70e903e713",
        ),
        (
            "entity_assigned_to_device",
            "device",
            "device-\N{GREEK SMALL LETTER ALPHA}",
            ca001_reference("device", "device-\N{GREEK SMALL LETTER ALPHA}"),
        ),
        (
            "entity_assigned_to_area",
            "area",
            "area.k\N{LATIN SMALL LETTER O WITH STROKE}kken",
            ca001_reference("area", "area.k\N{LATIN SMALL LETTER O WITH STROKE}kken"),
        ),
        (
            "entity_has_label",
            "label",
            "label:energy",
            ca001_reference("label", "label:energy"),
        ),
    ),
)
def test_each_supported_predicate_persists_with_exact_target_contract(
    tmp_path, predicate, target_kind, target_raw, expected_target
):
    path = tmp_path / f"{target_kind}.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, entity = prepare_scan(service)
    result = service.persist_relationships(relationship_request(
        start,
        relationship_input(
            predicate=predicate,
            target_kind=target_kind,
            target_raw=target_raw,
            expected_target_ref=expected_target,
        ),
    ))
    records = service.read_relationships(result).relationships[0]

    source_ref = entity.entities[0].opaque_reference
    persisted = result.relationships[0]
    assert persisted.target_ref == expected_target
    assert persisted.public_relationship_id == relationship_reference(
        predicate, source_ref, expected_target
    )
    assert records.relationship["source_entity_id"] == entity.entities[0].entity_id
    assert records.relationship["source_ref"] == source_ref
    assert records.current_state["status"] == "CURRENT"
    assert [item["event_kind"] for item in records.lifecycle_events] == ["CREATED"]
    assert records.lifecycle_audit["event_kind"] == "RELATIONSHIP_TRANSITIONED"
    assert records.audit_subject_links[0]["subject_kind"] == "RELATIONSHIP"
    assert records.audit_evidence_links[0]["observation_id"] == start.observation_ids[0]
    assert (records.target_registration is None) == (target_kind == "integration")
    service.shutdown()


def test_relationship_identity_uses_ordered_frozen_framing(tmp_path):
    path = tmp_path / "identity.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, entity = prepare_scan(service)
    result = service.persist_relationships(relationship_request(
        start, relationship_input(target_kind="device")
    )).relationships[0]

    expected_target = ca001_reference("device", "device-\N{GREEK SMALL LETTER ALPHA}")
    assert result.source_ref == entity.entities[0].opaque_reference
    assert result.target_ref == expected_target
    assert result.public_relationship_id == relationship_reference(
        "entity_assigned_to_device", result.source_ref, expected_target
    )
    assert result.public_relationship_id != relationship_reference(
        "entity_assigned_to_device", expected_target, result.source_ref
    )
    service.shutdown()


def test_multiple_relationships_are_deterministic_and_enumerable(tmp_path):
    path = tmp_path / "multiple.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, entity = prepare_scan(service)
    items = (
        relationship_input(
            key="platform", predicate="entity_uses_platform",
            target_kind="integration", target_raw="mqtt",
        ),
        relationship_input(key="device"),
        relationship_input(
            key="area", predicate="entity_assigned_to_area",
            target_kind="area", target_raw="private-area",
        ),
        relationship_input(
            key="label", predicate="entity_has_label",
            target_kind="label", target_raw="private-label",
        ),
    )
    result = service.persist_relationships(relationship_request(start, *items))
    by_installation = service.list_relationships_for_installation(start.installation_id)
    by_scan = service.list_relationships_for_scan(start.scan_run_id)
    by_source = service.list_relationships_for_source_entity(
        entity.entities[0].entity_id
    )
    service.shutdown()

    expected = sorted(item.public_relationship_id for item in result.relationships)
    assert [item["public_relationship_id"] for item in by_installation] == expected
    assert [item["public_relationship_id"] for item in by_scan] == expected
    assert [item["public_relationship_id"] for item in by_source] == expected


def test_equivalent_same_service_and_reconstructed_retry_are_noise_free(tmp_path):
    path = tmp_path / "retry.sqlite"
    request = None
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    request = relationship_request(start, relationship_input())
    first = service.persist_relationships(request)
    before = table_counts(path)
    assert service.persist_relationships(request) == first
    assert table_counts(path) == before
    service.shutdown()

    reconstructed = HaskDatabaseService(factory(path), FixedProvider())
    reconstructed.startup()
    assert reconstructed.persist_relationships(request) == first
    assert table_counts(path) == before
    reconstructed.shutdown()


def test_reversed_source_target_is_not_treated_as_symmetric(tmp_path):
    path = tmp_path / "direction.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    service.persist_relationships(relationship_request(start, relationship_input()))
    before = table_counts(path)

    with pytest.raises(NotFoundError):
        service.persist_relationships(relationship_request(
            start,
            relationship_input(
                key="reversed",
                source_raw="device-\N{GREEK SMALL LETTER ALPHA}",
                target_raw=SOURCE_RAW,
            ),
        ))
    assert table_counts(path) == before
    service.shutdown()


def test_changed_predicate_creates_a_distinct_identity(tmp_path):
    path = tmp_path / "predicate.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    result = service.persist_relationships(relationship_request(
        start,
        relationship_input(key="device", target_raw="shared-target"),
        relationship_input(
            key="area", predicate="entity_assigned_to_area",
            target_kind="area", target_raw="shared-target",
        ),
    ))
    service.shutdown()

    assert len({item.relationship_id for item in result.relationships}) == 2
    assert len({item.public_relationship_id for item in result.relationships}) == 2


def test_unknown_and_cross_installation_sources_are_rejected(tmp_path):
    path = tmp_path / "sources.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    first, _ = prepare_scan(service)
    with pytest.raises(NotFoundError):
        service.persist_relationships(relationship_request(
            first, relationship_input(source_raw="sensor.unknown")
        ))

    second, _ = prepare_scan(
        service,
        scan_key="other-installation-scan",
        started_at="2026-07-27T20:10:00Z",
        recovery_set_ref="recovery:other-installation",
        source_raw="sensor.other-installation",
    )
    with pytest.raises(NotFoundError):
        service.persist_relationships(relationship_request(
            second,
            relationship_input(source_raw=SOURCE_RAW),
            event_at="2026-07-27T20:10:00Z",
        ))
    service.shutdown()


def test_malformed_or_conflicting_protected_target_is_rejected(tmp_path):
    path = tmp_path / "target-validation.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    before = table_counts(path)

    with pytest.raises(ValidationFailureError):
        service.persist_relationships(relationship_request(
            start, relationship_input(expected_target_ref="refh1_device_not-a-digest")
        ))
    with pytest.raises(IdempotencyConflictError):
        service.persist_relationships(relationship_request(
            start,
            relationship_input(expected_target_ref="refh1_device_" + "0" * 64),
        ))
    assert table_counts(path) == before
    service.shutdown()


def test_invalid_later_relationship_rolls_back_complete_uow(tmp_path):
    path = tmp_path / "rollback.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    before = table_counts(path)

    with pytest.raises(NotFoundError):
        service.persist_relationships(relationship_request(
            start,
            relationship_input(key="first-valid"),
            relationship_input(key="second-invalid", source_raw="sensor.unknown"),
        ))
    assert table_counts(path) == before
    service.shutdown()


def test_unchanged_removal_recreation_and_absence_follow_frozen_lifecycle(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    first, _ = prepare_scan(service)
    initial = service.persist_relationships(relationship_request(
        first, relationship_input()
    ))
    assert table_counts(path)["relationship_lifecycle_event"] == 1

    second, _ = prepare_scan(
        service, scan_key="relationship-scan-2", started_at="2026-07-27T21:00:00Z"
    )
    unchanged = service.persist_relationships(relationship_request(
        second, relationship_input(), event_at="2026-07-27T21:00:00Z"
    ))
    assert unchanged.relationships[0].lifecycle_event_id == (
        initial.relationships[0].lifecycle_event_id
    )
    assert table_counts(path)["relationship_lifecycle_event"] == 1

    absence, _ = prepare_scan(
        service, scan_key="relationship-absence", started_at="2026-07-27T22:00:00Z"
    )
    del absence
    assert table_counts(path)["relationship_lifecycle_event"] == 1

    removal_scan, _ = prepare_scan(
        service, scan_key="relationship-removal", started_at="2026-07-27T23:00:00Z"
    )
    removed = service.persist_relationships(relationship_request(
        removal_scan,
        relationship_input(
            current_status="CURRENT_ABSENT",
            reason_code=RELATIONSHIP_REMOVAL_REASON,
        ),
        event_at="2026-07-27T23:00:00Z",
    ))
    assert removed.relationships[0].relationship_id == initial.relationships[0].relationship_id

    recreation_scan, _ = prepare_scan(
        service, scan_key="relationship-recreation", started_at="2026-07-28T00:00:00Z"
    )
    recreated = service.persist_relationships(relationship_request(
        recreation_scan,
        relationship_input(reason_code=RELATIONSHIP_RECREATION_REASON),
        event_at="2026-07-28T00:00:00Z",
    ))
    records = service.read_relationships(recreated).relationships[0]
    assert recreated.relationships[0].relationship_id == initial.relationships[0].relationship_id
    assert records.current_state["status"] == "CURRENT"
    assert [item["event_kind"] for item in records.lifecycle_events] == [
        "CREATED", "REMOVED", "RECREATED"
    ]
    service.shutdown()


def synthetic_model(*, explicit: bool = True) -> InstallationModel:
    raw_id = "sensor.private_source"
    registry = (
        {
            "entity_id": raw_id,
            "platform": "private-integration",
            "device_id": "private-device",
            "area_id": "private-area",
            "labels": ["private-label"],
        }
        if explicit
        else {"entity_id": raw_id}
    )
    entity = EntityModel(
        entity_id=raw_id,
        name="PROHIBITED FRIENDLY NAME",
        domain="sensor",
        platform="private-integration",
        state="PROHIBITED STATE",
        area_id="private-area",
        device_id="private-device",
        is_ignored=False,
        is_physical=True,
        attributes={"token": "PROHIBITED TOKEN"},
        registry=registry,
    )
    return InstallationModel(
        areas={}, devices={}, entities={raw_id: entity}, integrations={}, config={},
        states=[], services=[], labels=[], raw={},
    )


def app_config(path, backend_kind: str = "windows_credential_manager"):
    return {
        "hask_database_enabled": True,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "relationship-product",
        "hask_database_identity_version": 1,
        "hask_database_installation_uuid": "123e4567-e89b-42d3-a456-426614174000",
        "hask_database_installation_scope": SCOPE,
        "hask_database_secret_handle": HANDLE,
        "hask_database_secret_generation": 1,
        "hask_database_identity_state": "initialized",
        "hask_database_secret_backend": backend_kind,
    }


def test_disabled_mode_does_not_build_or_persist_relationships(tmp_path, monkeypatch):
    from hadocs.core import relationships

    def forbidden(*args, **kwargs):
        raise AssertionError("disabled mode built relationship candidates")

    monkeypatch.setattr(relationships, "build_relationship_candidates", forbidden)
    path = tmp_path / "disabled.sqlite"
    result = persist_operational_database(
        synthetic_model(),
        {"hask_database_enabled": False, "hask_database_path": str(path)},
        secret_provider=FixedProvider(),
    )
    assert result.eligible_relationship_count == 0
    assert result.persisted_relationship_count == 0
    assert result.ineligible_relationship_count == 0
    assert not path.exists()


def test_enabled_product_scan_is_entity_first_private_and_restart_safe(tmp_path, caplog):
    path = tmp_path / "product.sqlite"
    config = app_config(path)
    backend = MemoryBackend(SECRET, "windows_credential_manager")
    operation = OperationalDatabaseOperation(
        "relationship-product-operation",
        "2026-07-28T01:00:00Z",
        "2026-07-28T01:00:01Z",
    )
    first = persist_operational_database(
        synthetic_model(),
        config,
        operation=operation,
        secret_provider=CredentialStoreSecretProvider(backend),
    )
    replay = persist_operational_database(
        synthetic_model(),
        config,
        operation=operation,
        secret_provider=CredentialStoreSecretProvider(backend),
    )

    assert first.eligible_relationship_count == first.persisted_relationship_count == 4
    assert first.ineligible_relationship_count == 0
    assert replay.persisted_relationship_count == 4
    assert replay.replay_state == "existing_terminal"
    external = repr(first) + repr(replay) + caplog.text
    database = path.read_bytes()
    for prohibited in (
        "sensor.private_source",
        "private-integration",
        "private-device",
        "private-area",
        "private-label",
        "PROHIBITED FRIENDLY NAME",
        "PROHIBITED STATE",
        "PROHIBITED TOKEN",
    ):
        assert prohibited not in external
        assert prohibited.encode("utf-8") not in database

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("SELECT count(*) FROM entity").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship").fetchone()[0] == 4
        assert connection.execute(
            "SELECT count(*) FROM relationship_current_state WHERE status='CURRENT'"
        ).fetchone()[0] == 4
        entity_audit = connection.execute(
            "SELECT max(audit_id) FROM entity_lifecycle_event"
        ).fetchone()[0]
        relationship_audit = connection.execute(
            "SELECT min(audit_id) FROM relationship_lifecycle_event"
        ).fetchone()[0]
        assert relationship_audit > entity_audit
        assert connection.execute("SELECT status FROM scan_run").fetchone()[0] == "SUCCEEDED"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == SCHEMA_HASH
    finally:
        connection.close()


def test_ineligible_candidates_are_counted_but_not_persisted(tmp_path):
    path = tmp_path / "ineligible.sqlite"
    config = app_config(path)
    result = persist_operational_database(
        synthetic_model(explicit=False),
        config,
        operation=OperationalDatabaseOperation(
            "ineligible-operation",
            "2026-07-28T02:00:00Z",
            "2026-07-28T02:00:01Z",
        ),
        secret_provider=CredentialStoreSecretProvider(
            MemoryBackend(SECRET, "windows_credential_manager")
        ),
    )
    assert result.eligible_relationship_count == 0
    assert result.persisted_relationship_count == 0
    assert result.ineligible_relationship_count == 3
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("SELECT count(*) FROM relationship").fetchone()[0] == 0
    finally:
        connection.close()


def test_windows_and_posix_providers_produce_identical_relationships(tmp_path):
    outputs = []
    for backend_kind in ("windows_credential_manager", "posix_file"):
        path = tmp_path / f"{backend_kind}.sqlite"
        provider = CredentialStoreSecretProvider(
            MemoryBackend(SECRET, backend_kind)
        )
        service = HaskDatabaseService(factory(path), provider)
        service.startup()
        start, _ = prepare_scan(service)
        result = service.persist_relationships(relationship_request(
            start, relationship_input()
        )).relationships[0]
        outputs.append((result.target_ref, result.public_relationship_id))
        service.shutdown()
    assert outputs[0] == outputs[1]


def test_relationship_database_integrity_is_clean(tmp_path):
    path = tmp_path / "integrity.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start, _ = prepare_scan(service)
    service.persist_relationships(relationship_request(
        start, relationship_input()
    ))
    service.shutdown()

    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == SCHEMA_HASH
    finally:
        connection.close()
