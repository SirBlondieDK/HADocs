from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from hadocs.hask_database import (
    CapabilityOutcomeInput,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    IdempotencyConflictError,
    NotFoundError,
    ObservationInput,
    OperationalReplayState,
    OperationalSliceRequest,
    RepositoryOwner,
    SCAN_AUDIT_EVIDENCE_ROLE,
    SCAN_AUDIT_SUBJECT_ROLE,
    SCAN_COMPLETION_CONTRACT,
    ScanCompletionRequest,
    ScanCompletionIntent,
    SerializedTransactionManager,
    ValidationFailureError,
    initialize_batch2_schema,
    schema_sha256,
)


FROZEN_SCHEMA_SHA256 = "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"


def factory(path):
    return HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))


def strict_factory(path):
    return HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=path, expected_user_version=8)
    )


def start_request(suffix: str = "one") -> OperationalSliceRequest:
    return OperationalSliceRequest(
        recovery_set_ref=f"recovery:test-installation:{suffix}",
        installation_scope=f"home-assistant:test:{suffix}",
        secret_handle=f"secret-handle:test:{suffix}",
        secret_generation=1,
        context_format_version=1,
        scan_idempotency_key=f"scan:test:{suffix}",
        started_at="2026-07-27T12:00:00Z",
        implementation_version="batch-2",
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


def capability_outcomes() -> tuple[CapabilityOutcomeInput, ...]:
    return (
        CapabilityOutcomeInput(
            capability_id="core.collection",
            status="SUCCEEDED",
            retryable=None,
            safe_error_code=None,
            observation_contribution=True,
            completeness_contribution="PARTIAL",
        ),
        CapabilityOutcomeInput(
            capability_id="optional.failure",
            status="FAILED",
            retryable=True,
            safe_error_code="CAPABILITY_FAILED",
            observation_contribution=False,
            completeness_contribution="PARTIAL",
        ),
        CapabilityOutcomeInput(
            capability_id="optional.unavailable",
            status="UNAVAILABLE",
            retryable=False,
            safe_error_code=None,
            observation_contribution=False,
            completeness_contribution="NONE",
        ),
        CapabilityOutcomeInput(
            capability_id="optional.unsupported",
            status="UNSUPPORTED",
            retryable=None,
            safe_error_code=None,
            observation_contribution=False,
            completeness_contribution="NONE",
        ),
    )


def completion(started) -> ScanCompletionRequest:
    return ScanCompletionRequest(
        scan_run_id=started.scan_run_id,
        expected_installation_id=started.installation_id,
        completion_idempotency_key="completion:scan:test:one",
        terminal_at="2026-07-27T12:05:00Z",
        terminal_status="SUCCEEDED",
        completeness="PARTIAL",
        safe_error_code=None,
        capabilities=capability_outcomes(),
        observation_ids=started.observation_ids,
    )


def completion_intent() -> ScanCompletionIntent:
    return ScanCompletionIntent(
        completion_idempotency_key="completion:scan:test:one",
        terminal_at="2026-07-27T12:05:00Z",
        terminal_status="SUCCEEDED",
        completeness="PARTIAL",
        safe_error_code=None,
        capabilities=capability_outcomes(),
    )


class TracingFactory(HaskSQLiteConnectionFactory):
    def __init__(self, path):
        super().__init__(HaskDatabaseConfig(enabled=True, path=path))
        self.statements: list[str] = []

    def open_for_migration(self, target_user_version):
        managed = super().open_for_migration(target_user_version)
        managed.connection.set_trace_callback(self.statements.append)
        return managed


def completion_snapshot(path) -> dict[str, object]:
    connection = sqlite3.connect(path)
    try:
        scan_rows = tuple(connection.execute(
            "SELECT id,status,completeness,terminal_at,safe_error_code "
            "FROM scan_run ORDER BY id"
        ))
        counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "scan_capability_outcome",
                "audit_record",
                "audit_subject_link",
                "audit_evidence_link",
                "observation",
            )
        }
        return {"scans": scan_rows, "counts": counts}
    finally:
        connection.close()


def test_scan_completion_contract_is_explicit_and_limits_repository_participation():
    assert SCAN_COMPLETION_CONTRACT.name == "scan_completion"
    assert SCAN_COMPLETION_CONTRACT.permitted_starting_states == ("RUNNING",)
    assert set(SCAN_COMPLETION_CONTRACT.permitted_terminal_states) == {
        "SUCCEEDED",
        "FAILED",
        "INTERRUPTED",
        "CANCELLED",
    }
    assert SCAN_COMPLETION_CONTRACT.repository_owners == (
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    )

    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    initialize_batch2_schema(connection)
    manager = SerializedTransactionManager(connection)
    with manager.unit_of_work(SCAN_COMPLETION_CONTRACT) as unit:
        assert tuple(item.descriptor.owner for item in unit.repositories) == (
            RepositoryOwner.SCAN_RUN,
            RepositoryOwner.OBSERVATION,
            RepositoryOwner.AUDIT,
        )


def test_valid_completion_persists_capabilities_audit_links_and_terminal_state(tmp_path):
    path = tmp_path / "completion.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    request = completion(started)

    result = service.complete_scan(request)
    records = service.read_scan_completion(result)
    before_retry = completion_snapshot(path)
    retry = service.complete_scan(request)
    after_retry = completion_snapshot(path)

    assert retry == result
    assert before_retry == after_retry
    assert records.scan_run["status"] == "SUCCEEDED"
    assert records.scan_run["completeness"] == "PARTIAL"
    assert [item["status"] for item in records.capability_outcomes] == [
        "SUCCEEDED",
        "FAILED",
        "UNAVAILABLE",
        "UNSUPPORTED",
    ]
    assert records.audit["event_kind"] == "SCAN_TERMINATED"
    assert records.audit["idempotency_key"] == "completion:scan:test:one"
    assert [item["role"] for item in records.subject_links] == [
        SCAN_AUDIT_SUBJECT_ROLE
    ]
    assert [item["role"] for item in records.evidence_links] == [
        SCAN_AUDIT_EVIDENCE_ROLE,
        SCAN_AUDIT_EVIDENCE_ROLE,
    ]
    assert [item["ordinal"] for item in records.evidence_links] == [0, 1]
    assert before_retry["counts"] == {
        "scan_capability_outcome": 4,
        "audit_record": 3,
        "audit_subject_link": 1,
        "audit_evidence_link": 2,
        "observation": 2,
    }
    service.shutdown()

    with strict_factory(path).connect() as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256


def test_equivalent_completion_retry_survives_service_reconstruction(tmp_path):
    path = tmp_path / "restart.sqlite"
    first_service = HaskDatabaseService(factory(path))
    first_service.startup()
    started = first_service.persist_operational_slice(start_request())
    request = completion(started)
    first = first_service.complete_scan(request)
    first_snapshot = completion_snapshot(path)
    first_service.shutdown()

    reconstructed = HaskDatabaseService(factory(path))
    reconstructed.startup()
    retry = reconstructed.complete_scan(request)
    records = reconstructed.read_scan_completion(retry)
    reconstructed.shutdown()

    assert retry == first
    assert completion_snapshot(path) == first_snapshot
    assert len(records.capability_outcomes) == 4
    assert len(records.evidence_links) == 2


def test_terminal_replay_returns_original_ids_and_is_strictly_read_only(tmp_path):
    path = tmp_path / "terminal-replay.sqlite"
    first_factory = TracingFactory(path)
    service = HaskDatabaseService(first_factory)
    service.startup()
    started = service.persist_operational_slice(start_request())
    completed = service.complete_scan(completion(started))
    snapshot = completion_snapshot(path)

    first_factory.statements.clear()
    same_service = service.start_or_replay_operational_slice(
        start_request(), completion_intent=completion_intent()
    )
    same_service_statements = tuple(first_factory.statements)
    service.shutdown()

    reconstructed_factory = TracingFactory(path)
    reconstructed = HaskDatabaseService(reconstructed_factory)
    reconstructed.startup()
    reconstructed_factory.statements.clear()
    after_restart = reconstructed.start_or_replay_operational_slice(
        start_request(), completion_intent=completion_intent()
    )
    restart_statements = tuple(reconstructed_factory.statements)
    reconstructed.shutdown()

    assert same_service.state is OperationalReplayState.EXISTING_TERMINAL
    assert after_restart.state is OperationalReplayState.EXISTING_TERMINAL
    assert same_service.operational_slice == started
    assert after_restart.operational_slice == started
    assert same_service.completion == completed
    assert after_restart.completion == completed
    assert completion_snapshot(path) == snapshot
    for statements in (same_service_statements, restart_statements):
        assert statements
        assert not any(
            statement.lstrip().upper().startswith(
                ("BEGIN", "INSERT", "UPDATE", "DELETE", "REPLACE")
            )
            for statement in statements
        )
    with strict_factory(path).connect() as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256


def test_terminal_replay_rejects_terminal_and_capability_conflicts(tmp_path):
    path = tmp_path / "terminal-replay-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    service.complete_scan(completion(started))
    before = completion_snapshot(path)
    intent = completion_intent()
    changed_capability = replace(
        intent.capabilities[-1],
        status="UNAVAILABLE",
        retryable=False,
        completeness_contribution="NONE",
    )
    changed_observation = replace(
        start_request().observations[0],
        payload={"count": 999, "category": "integration"},
    )

    with pytest.raises(IdempotencyConflictError, match="terminal"):
        service.start_or_replay_operational_slice(
            start_request(),
            completion_intent=replace(
                intent,
                terminal_status="FAILED",
                safe_error_code="SCAN_FAILED",
            ),
        )
    with pytest.raises(IdempotencyConflictError, match="capability"):
        service.start_or_replay_operational_slice(
            start_request(),
            completion_intent=replace(
                intent,
                capabilities=(*intent.capabilities[:-1], changed_capability),
            ),
        )
    with pytest.raises(IdempotencyConflictError, match="observation"):
        service.start_or_replay_operational_slice(
            replace(
                start_request(),
                observations=(
                    changed_observation,
                    start_request().observations[1],
                ),
            ),
            completion_intent=intent,
        )

    assert completion_snapshot(path) == before
    service.shutdown()


def test_terminal_replay_rejects_partial_terminal_artifacts(tmp_path):
    path = tmp_path / "terminal-replay-partial.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    service.shutdown()

    with strict_factory(path).connect() as connection:
        connection.execute(
            "UPDATE scan_run SET terminal_at=?,status='SUCCEEDED',completeness='PARTIAL' "
            "WHERE id=? AND status='RUNNING'",
            ("2026-07-27T12:05:00Z", started.scan_run_id),
        )

    reconstructed = HaskDatabaseService(factory(path))
    reconstructed.startup()
    with pytest.raises(ValidationFailureError, match="observation evidence"):
        reconstructed.start_or_replay_operational_slice(
            start_request(), completion_intent=completion_intent()
        )
    reconstructed.shutdown()

    with strict_factory(path).connect() as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256


def test_conflicting_terminal_state_is_rejected_without_changes(tmp_path):
    path = tmp_path / "terminal-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    request = completion(started)
    service.complete_scan(request)
    before = completion_snapshot(path)

    with pytest.raises(IdempotencyConflictError, match="terminal"):
        service.complete_scan(
            replace(
                request,
                terminal_status="FAILED",
                completeness="PARTIAL",
                safe_error_code="SCAN_FAILED",
            )
        )

    assert completion_snapshot(path) == before
    service.shutdown()


def test_conflicting_capability_intent_is_rejected_without_changes(tmp_path):
    path = tmp_path / "capability-conflict.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    request = completion(started)
    service.complete_scan(request)
    before = completion_snapshot(path)
    changed = replace(
        request.capabilities[-1],
        status="UNAVAILABLE",
        retryable=False,
        completeness_contribution="NONE",
    )

    with pytest.raises(IdempotencyConflictError, match="capability"):
        service.complete_scan(
            replace(request, capabilities=(*request.capabilities[:-1], changed))
        )

    assert completion_snapshot(path) == before
    service.shutdown()


def test_missing_scan_and_wrong_installation_are_rejected(tmp_path):
    path = tmp_path / "ownership.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    with pytest.raises(NotFoundError, match="does not exist"):
        service.complete_scan(
            ScanCompletionRequest(
                scan_run_id=999,
                expected_installation_id=999,
                completion_idempotency_key="completion:missing",
                terminal_at="2026-07-27T12:05:00Z",
                terminal_status="SUCCEEDED",
                completeness="PARTIAL",
                safe_error_code=None,
                capabilities=capability_outcomes(),
                observation_ids=(999,),
            )
        )

    started = service.persist_operational_slice(start_request())
    before = completion_snapshot(path)
    with pytest.raises(ValidationFailureError, match="expected installation"):
        service.complete_scan(
            replace(completion(started), expected_installation_id=started.installation_id + 1)
        )
    assert completion_snapshot(path) == before
    service.shutdown()


def test_observation_from_another_scan_is_rejected_before_writes(tmp_path):
    path = tmp_path / "observation-ownership.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    first = service.persist_operational_slice(start_request("one"))
    second = service.persist_operational_slice(start_request("two"))
    request = completion(first)
    wrong_ids = (second.observation_ids[0], first.observation_ids[1])
    before = completion_snapshot(path)

    with pytest.raises(ValidationFailureError, match="different scan"):
        service.complete_scan(replace(request, observation_ids=wrong_ids))

    assert completion_snapshot(path) == before
    service.shutdown()


def test_duplicate_capability_and_invalid_terminal_shape_leave_state_unchanged(tmp_path):
    path = tmp_path / "validation-rollback.sqlite"
    service = HaskDatabaseService(factory(path))
    service.startup()
    started = service.persist_operational_slice(start_request())
    request = completion(started)
    before = completion_snapshot(path)

    with pytest.raises(ValidationFailureError, match="identities must be unique"):
        service.complete_scan(
            replace(request, capabilities=(request.capabilities[0], request.capabilities[0]))
        )
    with pytest.raises(ValidationFailureError, match="scan intent"):
        service.complete_scan(replace(request, completeness="COMPLETE"))

    assert completion_snapshot(path) == before
    assert before["scans"] == ((started.scan_run_id, "RUNNING", "PENDING", None, None),)
    assert before["counts"] == {
        "scan_capability_outcome": 0,
        "audit_record": 2,
        "audit_subject_link": 0,
        "audit_evidence_link": 0,
        "observation": 2,
    }
    service.shutdown()
