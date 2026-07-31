from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from hadocs.hask_database import (
    ConstraintViolationError,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    IdempotencyConflictError,
    ObservationInput,
    OperationalReplayState,
    OperationalSliceRequest,
    ServiceState,
    schema_sha256,
)


FROZEN_SCHEMA_SHA256 = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"


def factory(path):
    return HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))


def request() -> OperationalSliceRequest:
    return OperationalSliceRequest(
        recovery_set_ref="recovery:test-installation",
        installation_scope="home-assistant:test",
        secret_handle="secret-handle:test",
        secret_generation=1,
        context_format_version=1,
        scan_idempotency_key="scan:test-001",
        started_at="2026-07-27T12:00:00Z",
        implementation_version="batch-1",
        contract_version="hadocs-generic-metadata-1.0.0",
        observations=(
            ObservationInput(
                observation_key="observation:integration-count",
                taxonomy_class="B",
                authority_class="STRUCTURED_CONTEXT_DEPENDENT",
                observed_at="2026-07-27T12:00:01Z",
                payload={"count": 2, "category": "integration"},
                privacy_class="LOCAL_ONLY",
                retention_policy="RETAIN_UNTIL_SUPERSEDED",
            ),
            ObservationInput(
                observation_key="observation:entity-count",
                taxonomy_class="B",
                authority_class="STRUCTURED_CONTEXT_DEPENDENT",
                observed_at="2026-07-27T12:00:02Z",
                payload={"category": "entity", "count": 12},
                privacy_class="LOCAL_ONLY",
                retention_policy="RETAIN_UNTIL_SUPERSEDED",
            ),
        ),
    )


def strict_connection(path):
    return HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=path, expected_user_version=8)
    )


def test_atomic_slice_is_repository_readable_and_same_service_retry_is_identical(tmp_path):
    path = tmp_path / "operational.sqlite"
    service = HaskDatabaseService(factory(path), clock=lambda: "2026-07-27T12:10:00Z")
    assert service.startup().state == ServiceState.ACTIVE
    assert not hasattr(service, "connection")

    first = service.persist_operational_slice(request())
    records = service.read_operational_slice(first)
    retry = service.persist_operational_slice(request())

    assert retry == first
    assert records.installation["recovery_set_ref"] == "recovery:test-installation"
    assert records.context["installation_scope"] == "home-assistant:test"
    assert records.scan_run["status"] == "RUNNING"
    assert [item["event_kind"] for item in records.audits] == [
        "INSTALLATION_CREATED",
        "CONTEXT_ACTIVATED",
    ]
    assert len(records.observations) == 2
    assert records.observations[0]["normalized_payload_json"] == (
        '{"category":"integration","count":2}'
    )
    assert records.observations[0]["immutable_digest"] == hashlib.sha256(
        b'{"category":"integration","count":2}'
    ).digest()
    service.shutdown()

    with strict_connection(path).connect() as connection:
        assert {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "logical_installation",
                "installation_context",
                "audit_record",
                "scan_run",
                "observation",
            )
        } == {
            "logical_installation": 1,
            "installation_context": 1,
            "audit_record": 2,
            "scan_run": 1,
            "observation": 2,
        }
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_reconstructed_service_returns_same_semantic_result_without_duplicates(tmp_path):
    path = tmp_path / "restart.sqlite"
    first_service = HaskDatabaseService(factory(path), clock=lambda: "first-persisted-time")
    first_service.startup()
    first = first_service.persist_operational_slice(request())
    first_service.shutdown()

    reconstructed = HaskDatabaseService(factory(path), clock=lambda: "different-retry-time")
    assert reconstructed.startup().state == ServiceState.ACTIVE
    retry = reconstructed.persist_operational_slice(request())
    records = reconstructed.read_operational_slice(retry)
    reconstructed.shutdown()

    assert retry == first
    assert len(records.audits) == 2
    assert len(records.observations) == 2
    with strict_connection(path).connect() as connection:
        assert connection.execute("SELECT count(*) FROM scan_run").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM observation").fetchone()[0] == 2


def test_start_or_replay_distinguishes_new_and_running_retries(tmp_path):
    path = tmp_path / "start-or-replay.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()

    created = service.start_or_replay_operational_slice(request())
    same_service = service.start_or_replay_operational_slice(request())
    service.shutdown()

    reconstructed = HaskDatabaseService(factory(path))
    reconstructed.startup()
    after_restart = reconstructed.start_or_replay_operational_slice(request())
    reconstructed.shutdown()

    assert created.state is OperationalReplayState.NEW_RUNNING
    assert same_service.state is OperationalReplayState.EXISTING_RUNNING
    assert after_restart.state is OperationalReplayState.EXISTING_RUNNING
    assert created.operational_slice == same_service.operational_slice
    assert created.operational_slice == after_restart.operational_slice
    assert created.completion is None
    assert same_service.completion is None
    assert after_restart.completion is None
    with strict_connection(path).connect() as connection:
        assert connection.execute("SELECT count(*) FROM scan_run").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM observation").fetchone()[0] == 2


def test_start_or_replay_rejects_running_scan_and_observation_conflicts(tmp_path):
    path = tmp_path / "start-or-replay-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    created = service.start_or_replay_operational_slice(request())
    changed_observation = replace(
        request().observations[0],
        payload={"count": 999, "category": "integration"},
    )

    with pytest.raises(IdempotencyConflictError, match="scan run"):
        service.start_or_replay_operational_slice(
            replace(request(), started_at="2026-07-27T13:00:00Z")
        )
    with pytest.raises(IdempotencyConflictError, match="observation"):
        service.start_or_replay_operational_slice(
            replace(
                request(),
                observations=(changed_observation, request().observations[1]),
            )
        )

    assert service.start_or_replay_operational_slice(request()).operational_slice == (
        created.operational_slice
    )
    service.shutdown()


def test_changed_scan_intent_under_existing_key_fails_without_duplication(tmp_path):
    path = tmp_path / "scan-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    first = service.persist_operational_slice(request())

    with pytest.raises(IdempotencyConflictError, match="scan run"):
        service.persist_operational_slice(
            replace(request(), started_at="2026-07-27T13:00:00Z")
        )

    assert service.persist_operational_slice(request()) == first
    service.shutdown()


def test_changed_observation_payload_under_existing_key_fails(tmp_path):
    path = tmp_path / "observation-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    first_request = request()
    service.persist_operational_slice(first_request)
    changed = replace(
        first_request.observations[0],
        payload={"count": 999, "category": "integration"},
    )

    with pytest.raises(IdempotencyConflictError, match="observation"):
        service.persist_operational_slice(
            replace(first_request, observations=(changed, first_request.observations[1]))
        )
    service.shutdown()


def test_invalid_observation_rolls_back_installation_audits_context_run_and_observations(tmp_path):
    path = tmp_path / "rollback.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    invalid = replace(request().observations[0], taxonomy_class="INVALID")

    with pytest.raises(ConstraintViolationError):
        service.persist_operational_slice(replace(request(), observations=(invalid,)))
    service.shutdown()

    with strict_connection(path).connect() as connection:
        for table in (
            "logical_installation",
            "installation_context",
            "audit_record",
            "scan_run",
            "observation",
        ):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
