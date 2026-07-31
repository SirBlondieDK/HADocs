from __future__ import annotations

import json
import sqlite3

import pytest

from hadocs.application.operational_database import (
    OperationalDatabaseOperation,
    persist_operational_database,
)
from hadocs.core.models import EntityModel, InstallationModel
from hadocs.hask_database import (
    CredentialStoreSecretProvider,
    ENTITY_REMOVAL_REASON,
    EntityPersistenceInput,
    EntityPersistenceRequest,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    IdempotencyConflictError,
    ObservationInput,
    OperationalSliceRequest,
    ValidationFailureError,
    derive_installation_scope,
    schema_sha256,
)


SCHEMA_HASH = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"
SCOPE = "is1_" + "a" * 64
SECRET = bytes(range(32))
HANDLE = f"HADocs/DatabaseIdentity/{SCOPE}/1"


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
    backend_kind = "windows_credential_manager"

    def __init__(self, secret: bytes) -> None:
        self.values = {HANDLE: secret}
        self.reads = 0

    def write(self, handle: str, value: bytes) -> None:
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        self.reads += 1
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


def factory(path):
    return HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))


def start_request(*, scan_key: str = "scan-1", started_at: str = "2026-07-27T15:00:00Z"):
    return OperationalSliceRequest(
        recovery_set_ref="recovery:entity-tests",
        installation_scope=SCOPE,
        secret_handle=HANDLE,
        secret_generation=1,
        context_format_version=1,
        scan_idempotency_key=scan_key,
        started_at=started_at,
        implementation_version="entity-batch-4a",
        contract_version="entity-persistence-v1",
        observations=(ObservationInput(
            observation_key="normalized-counts",
            taxonomy_class="B",
            authority_class="STRUCTURED_CONTEXT_DEPENDENT",
            observed_at=started_at,
            payload={"entities": 2},
            privacy_class="LOCAL_ONLY",
            retention_policy="RETAIN_UNTIL_SUPERSEDED",
        ),),
    )


def entity_request(start, *items, event_at: str | None = None):
    return EntityPersistenceRequest(
        installation_id=start.installation_id,
        context_id=start.context_id,
        scan_run_id=start.scan_run_id,
        observation_id=start.observation_ids[0],
        event_at=event_at or "2026-07-27T15:00:00Z",
        entities=tuple(items),
    )


def counts(path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "collision_registry", "identity_registration", "entity",
                "entity_current_state", "entity_lifecycle_event", "audit_record",
                "audit_subject_link", "audit_evidence_link",
            )
        }
    finally:
        connection.close()


def test_one_entity_exact_ca001_vector_readback_and_retries(tmp_path):
    path = tmp_path / "entity.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start = service.persist_operational_slice(start_request())
    request = entity_request(start, EntityPersistenceInput(
        entity_key="entity-000000",
        raw_entity_id="sensor.kitchen_temperature",
    ))
    first = service.persist_entities(request)
    first_counts = counts(path)
    same = service.persist_entities(request)
    records = service.read_entities(first)

    expected = "refh1_entity_312675c4bb1c9ddc1caffc38c97bf0bc686bfb45909d60cd0d629355a296352d"
    assert same == first
    assert first.entities[0].opaque_reference == expected
    assert records.entities[0].registration["opaque_reference"] == expected
    assert records.entities[0].registration["identity_digest"] == bytes.fromhex(expected[-64:])
    assert records.entities[0].entity["identity_status"] == "ACTIVE"
    assert records.entities[0].current_state["lifecycle_state"] == "ACTIVE"
    assert len(records.entities[0].lifecycle_events) == 1
    assert records.entities[0].registration_audit["event_kind"] == "IDENTITY_REGISTERED"
    assert records.entities[0].lifecycle_audit["event_kind"] == "ENTITY_TRANSITIONED"
    assert counts(path) == first_counts
    service.shutdown()

    reconstructed = HaskDatabaseService(factory(path), FixedProvider())
    reconstructed.startup()
    assert reconstructed.persist_entities(request) == first
    assert counts(path) == first_counts
    reconstructed.shutdown()


def test_multiple_entities_are_deterministic_and_enumerable(tmp_path):
    path = tmp_path / "multiple.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start = service.persist_operational_slice(start_request())
    result = service.persist_entities(entity_request(
        start,
        EntityPersistenceInput("entity-000000", "sensor.kitchen_temperature"),
        EntityPersistenceInput("entity-000001", "light.synthetic_lamp"),
    ))
    listed = service.list_entities_for_installation(start.installation_id)
    service.shutdown()

    assert len(result.entities) == len(listed) == 2
    assert [row["opaque_reference"] for row in listed] == sorted(
        item.opaque_reference for item in result.entities
    )


@pytest.mark.parametrize(
    "backend_kind", ("windows_credential_manager", "posix_file")
)
def test_provider_backends_produce_identical_ca001_identity(tmp_path, backend_kind):
    path = tmp_path / f"{backend_kind}.sqlite"
    backend = MemoryBackend(SECRET)
    backend.backend_kind = backend_kind
    provider = CredentialStoreSecretProvider(backend)
    service = HaskDatabaseService(factory(path), provider)
    service.startup()
    start = service.persist_operational_slice(start_request())
    result = service.persist_entities(entity_request(
        start, EntityPersistenceInput("entity-000000", "sensor.kitchen_temperature")
    ))
    service.shutdown()
    assert result.entities[0].opaque_reference == (
        "refh1_entity_312675c4bb1c9ddc1caffc38c97bf0bc"
        "686bfb45909d60cd0d629355a296352d"
    )


def test_conflicting_identity_intent_rolls_back(tmp_path):
    path = tmp_path / "conflict.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start = service.persist_operational_slice(start_request())
    first_request = entity_request(
        start, EntityPersistenceInput("stable-slot", "sensor.kitchen_temperature")
    )
    service.persist_entities(first_request)
    before = counts(path)

    with pytest.raises(IdempotencyConflictError):
        service.persist_entities(entity_request(
            start, EntityPersistenceInput("stable-slot", "sensor.different")
        ))
    assert counts(path) == before
    service.shutdown()


def test_invalid_later_entity_rolls_back_complete_uow(tmp_path):
    path = tmp_path / "rollback.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    start = service.persist_operational_slice(start_request())

    with pytest.raises(ValidationFailureError):
        service.persist_entities(entity_request(
            start,
            EntityPersistenceInput("entity-000000", "sensor.valid"),
            EntityPersistenceInput(
                "entity-000001", "sensor.cannot_start_removed",
                lifecycle_state="REMOVED", reason_code=ENTITY_REMOVAL_REASON,
            ),
        ))
    persisted = counts(path)
    assert persisted["collision_registry"] == 0
    assert persisted["identity_registration"] == 0
    assert persisted["entity"] == 0
    assert persisted["entity_current_state"] == 0
    assert persisted["entity_lifecycle_event"] == 0
    assert persisted["audit_record"] == 2
    service.shutdown()


def test_unchanged_is_noise_free_and_explicit_removal_transitions(tmp_path):
    path = tmp_path / "transition.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    first_scan = service.persist_operational_slice(start_request())
    service.persist_entities(entity_request(
        first_scan, EntityPersistenceInput("entity-000000", "sensor.lifecycle")
    ))
    after_initial = counts(path)

    second_scan = service.persist_operational_slice(start_request(
        scan_key="scan-2", started_at="2026-07-27T16:00:00Z"
    ))
    unchanged = service.persist_entities(entity_request(
        second_scan,
        EntityPersistenceInput("entity-000000", "sensor.lifecycle"),
        event_at="2026-07-27T16:00:00Z",
    ))
    assert counts(path)["entity_lifecycle_event"] == after_initial["entity_lifecycle_event"]

    third_scan = service.persist_operational_slice(start_request(
        scan_key="scan-3", started_at="2026-07-27T17:00:00Z"
    ))
    removed = service.persist_entities(entity_request(
        third_scan,
        EntityPersistenceInput(
            "entity-000000", "sensor.lifecycle",
            lifecycle_state="REMOVED", reason_code=ENTITY_REMOVAL_REASON,
        ),
        event_at="2026-07-27T17:00:00Z",
    ))
    records = service.read_entities(removed).entities[0]
    assert unchanged.entities[0].lifecycle_event_id != removed.entities[0].lifecycle_event_id
    assert records.current_state["lifecycle_state"] == "REMOVED"
    assert [row["result_state"] for row in records.lifecycle_events] == ["ACTIVE", "REMOVED"]
    assert records.lifecycle_events[-1]["prior_state"] == "ACTIVE"
    service.shutdown()


def test_absence_alone_creates_no_transition_and_database_is_clean(tmp_path):
    path = tmp_path / "absence.sqlite"
    service = HaskDatabaseService(factory(path), FixedProvider())
    service.startup()
    first = service.persist_operational_slice(start_request())
    result = service.persist_entities(entity_request(
        first, EntityPersistenceInput("entity-000000", "sensor.absent_later")
    ))
    before = counts(path)["entity_lifecycle_event"]
    service.persist_operational_slice(start_request(
        scan_key="absence-only", started_at="2026-07-27T18:00:00Z"
    ))
    records = service.read_entities(result).entities[0]
    assert counts(path)["entity_lifecycle_event"] == before
    assert records.current_state["lifecycle_state"] == "ACTIVE"
    service.shutdown()

    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == SCHEMA_HASH
    finally:
        connection.close()


def synthetic_model(raw_ids: tuple[str, ...]) -> InstallationModel:
    entities = {
        raw_id: EntityModel(
            entity_id=raw_id,
            name="PROHIBITED FRIENDLY NAME",
            domain="sensor",
            platform="PROHIBITED PLATFORM",
            state="PROHIBITED STATE",
            area_id="PROHIBITED AREA",
            device_id="PROHIBITED DEVICE",
            is_ignored=False,
            is_physical=True,
            attributes={"token": "PROHIBITED TOKEN"},
        )
        for raw_id in raw_ids
    }
    return InstallationModel(
        areas={}, devices={}, entities=entities, integrations={}, config={},
        states=[], services=[], labels=[], raw={},
    )


def app_config(path) -> dict[str, object]:
    installation_uuid = "123e4567-e89b-42d3-a456-426614174000"
    actual_scope = derive_installation_scope(installation_uuid)
    return {
        "hask_database_enabled": True,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "synthetic-product",
        "hask_database_identity_version": 1,
        "hask_database_installation_uuid": installation_uuid,
        "hask_database_installation_scope": actual_scope,
        "hask_database_secret_handle": f"HADocs/DatabaseIdentity/{actual_scope}/1",
        "hask_database_secret_generation": 1,
        "hask_database_identity_state": "initialized",
        "hask_database_secret_backend": "windows_credential_manager",
    }


def test_disabled_mode_does_not_access_provider_or_create_database(tmp_path):
    class FailingProvider:
        def load(self, *args):
            raise AssertionError("disabled mode accessed protected provider")

    path = tmp_path / "disabled.sqlite"
    result = persist_operational_database(
        synthetic_model(("sensor.disabled",)),
        {"hask_database_enabled": False, "hask_database_path": str(path)},
        secret_provider=FailingProvider(),
    )
    assert result.state.value == "disabled"
    assert not path.exists()


def test_enabled_product_scan_persists_only_permitted_entity_material(tmp_path, caplog):
    path = tmp_path / "product.sqlite"
    config = app_config(path)
    handle = str(config["hask_database_secret_handle"])
    backend = MemoryBackend(SECRET)
    backend.values = {handle: SECRET}
    provider = CredentialStoreSecretProvider(backend)
    raw_ids = ("sensor.private_alpha", "light.private_beta")
    operation = OperationalDatabaseOperation(
        "entity-product-operation",
        "2026-07-27T19:00:00Z",
        "2026-07-27T19:00:01Z",
    )
    first = persist_operational_database(
        synthetic_model(raw_ids), config, operation=operation, secret_provider=provider
    )
    replay = persist_operational_database(
        synthetic_model(tuple(reversed(raw_ids))), config, operation=operation,
        secret_provider=CredentialStoreSecretProvider(backend),
    )

    assert first.entity_ids == replay.entity_ids
    assert first.entity_references == replay.entity_references
    assert len(first.entity_ids) == 2
    assert len(first.observation_ids) == 1
    assert replay.replay_state == "existing_terminal"
    database = path.read_bytes()
    external = (repr(first) + repr(replay) + caplog.text).encode("utf-8")
    for prohibited in (
        *raw_ids,
        "PROHIBITED FRIENDLY NAME", "PROHIBITED PLATFORM", "PROHIBITED STATE",
        "PROHIBITED AREA", "PROHIBITED DEVICE", "PROHIBITED TOKEN",
    ):
        encoded = prohibited.encode("utf-8")
        assert encoded not in database
        assert encoded not in external

    connection = sqlite3.connect(path)
    try:
        payloads = [row[0] for row in connection.execute(
            "SELECT normalized_payload_json FROM observation"
        )]
        assert payloads == [json.dumps(
            {"areas": 0, "devices": 0, "entities": 2, "integrations": 0},
            sort_keys=True, separators=(",", ":"),
        )]
        assert connection.execute("SELECT count(*) FROM entity").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM observation").fetchone()[0] == 1
        assert connection.execute("SELECT status FROM scan_run").fetchone()[0] == "SUCCEEDED"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()
