from __future__ import annotations

import sqlite3
import inspect

import pytest

from hadocs.hask_database import (
    AlreadyExistsError, BundleMismatchError, ConcurrencyConflictError,
    ConstraintViolationError, CorruptionDetectedError, FROZEN_OWNERSHIP,
    IdempotencyConflictError, IdempotencyCoordinator, NestedTransactionError,
    NotFoundError, RecoveryCoordinator, RecoveryModeError, RecoveryState,
    RepositoryError, RepositoryFactory, RepositoryMigrationFailureError,
    RepositoryOwner, RepositoryRegistry, RepositorySecretUnavailableError,
    RetryPolicy, SerializedTransactionManager, StorageFailureError,
    ValidationFailureError, VersionIncompatibleError, canonical_intent_digest,
    default_repository_registry, initialize_batch2_schema, schema_sha256,
    translate_sqlite_error, validate_frozen_ownership,
)


def migrated() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    initialize_batch2_schema(connection)
    return connection


def test_registry_contains_exactly_ten_frozen_owners():
    registry = default_repository_registry()
    assert len(registry.owners) == 10
    assert set(registry.owners) == set(RepositoryOwner)


def test_repository_ownership_covers_each_frozen_table_once():
    connection = migrated()
    tables = frozenset(
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    )
    validate_frozen_ownership(tables)
    flattened = [table for owned in FROZEN_OWNERSHIP.values() for table in owned]
    assert len(flattened) == len(set(flattened)) == 25


def test_registry_rejects_duplicate_and_incomplete_registration():
    registry = RepositoryRegistry()
    repository_type = default_repository_registry().resolve_type(RepositoryOwner.AUDIT)
    registry.register(repository_type)
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(repository_type)
    with pytest.raises(ValueError, match="exactly"):
        registry.validate_complete()


def test_factory_resolves_all_repositories_with_uow_lifetime_and_no_persistence_permission():
    repositories = RepositoryFactory().create_all(migrated())
    operational = {
        RepositoryOwner.LOGICAL_INSTALLATION,
        RepositoryOwner.COLLISION_REGISTRY,
        RepositoryOwner.ENTITY,
        RepositoryOwner.RELATIONSHIP,
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    }
    assert set(repositories) == set(RepositoryOwner)
    for owner, repository in repositories.items():
        assert repository.descriptor.owner is owner
        assert repository.descriptor.tables == FROZEN_OWNERSHIP[owner]
        assert repository.descriptor.lifetime == "UNIT_OF_WORK"
        assert repository.descriptor.permits_business_persistence is (owner in operational)


def test_only_authorized_repositories_expose_operational_calls():
    connection = migrated()
    manager = SerializedTransactionManager(connection)
    assert not hasattr(manager, "connection")
    operational = {
        RepositoryOwner.LOGICAL_INSTALLATION,
        RepositoryOwner.COLLISION_REGISTRY,
        RepositoryOwner.ENTITY,
        RepositoryOwner.RELATIONSHIP,
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    }
    for owner, repository in RepositoryFactory().create_all(connection).items():
        public_calls = [
            name for name, member in inspect.getmembers(repository, callable)
            if not name.startswith("_")
        ]
        assert bool(public_calls) is (owner in operational)


def test_unit_of_work_commits_and_releases_repositories():
    connection = migrated()
    manager = SerializedTransactionManager(connection)
    unit = manager.unit_of_work()
    with unit as active:
        assert connection.in_transaction
        assert len(active.repositories) == 10
        assert active.repository(RepositoryOwner.ENTITY).descriptor.owner is RepositoryOwner.ENTITY
    assert not connection.in_transaction
    with pytest.raises(NestedTransactionError):
        unit.repository(RepositoryOwner.ENTITY)


def test_unit_of_work_rolls_back_on_failure():
    connection = migrated()
    manager = SerializedTransactionManager(connection)
    with pytest.raises(RuntimeError, match="synthetic"):
        with manager.unit_of_work():
            assert connection.in_transaction
            raise RuntimeError("synthetic")
    assert not connection.in_transaction


def test_nested_unit_of_work_is_rejected_without_releasing_outer_owner():
    connection = migrated()
    manager = SerializedTransactionManager(connection)
    with manager.unit_of_work():
        with pytest.raises(NestedTransactionError):
            with manager.unit_of_work():
                pass
        assert connection.in_transaction


def test_recovery_mode_blocks_transactions_until_validation_passes():
    recovery = RecoveryCoordinator()
    manager = SerializedTransactionManager(migrated(), recovery=recovery)
    recovery.require_recovery()
    with pytest.raises(RecoveryModeError):
        with manager.unit_of_work():
            pass
    recovery.begin_validation()
    recovery.validation_passed()
    with manager.unit_of_work():
        assert recovery.state is RecoveryState.NORMAL


def test_failed_recovery_validation_remains_fail_closed():
    recovery = RecoveryCoordinator()
    recovery.require_recovery()
    recovery.begin_validation()
    recovery.validation_failed()
    assert recovery.state is RecoveryState.RECOVERY_REQUIRED
    with pytest.raises(RecoveryModeError):
        recovery.assert_writable()


def test_idempotency_is_deterministic_and_conflicts_fail_closed():
    coordinator = IdempotencyCoordinator()
    assert coordinator.claim("scan", "request-1", {"b": 2, "a": 1}) is True
    assert coordinator.claim("scan", "request-1", {"a": 1, "b": 2}) is False
    with pytest.raises(IdempotencyConflictError):
        coordinator.claim("scan", "request-1", {"a": 2, "b": 2})
    assert canonical_intent_digest({"b": 2, "a": 1}) == canonical_intent_digest({"a": 1, "b": 2})


def test_retry_policy_is_bounded_and_deterministic():
    policy = RetryPolicy()
    assert policy.attempts == 4
    assert policy.delays_ms == (25, 57, 119)
    assert sum(policy.delays_ms) <= policy.timeout_ms == 500
    with pytest.raises(ValueError):
        RetryPolicy(attempts=3)


class BusyConnection:
    def __init__(self, connection: sqlite3.Connection, busy_failures: int) -> None:
        self.connection = connection
        self.busy_failures = busy_failures
        self.begin_attempts = 0

    def execute(self, sql, parameters=()):
        if sql == "BEGIN IMMEDIATE":
            self.begin_attempts += 1
            if self.begin_attempts <= self.busy_failures:
                raise sqlite3.OperationalError("database is busy")
        return self.connection.execute(sql, parameters)

    def commit(self):
        return self.connection.commit()

    def rollback(self):
        return self.connection.rollback()


@pytest.mark.parametrize("busy_failures", [0, 1, 2, 3])
def test_busy_retry_uses_each_configured_delay_before_success(busy_failures):
    sleeps = []
    connection = BusyConnection(migrated(), busy_failures)
    manager = SerializedTransactionManager(connection, sleeper=sleeps.append)

    with manager.unit_of_work():
        pass

    assert connection.begin_attempts == busy_failures + 1
    assert sleeps == [0.025, 0.057, 0.119][:busy_failures]


def test_busy_retry_exhaustion_uses_all_delays_and_never_opens_transaction():
    sleeps = []
    connection = BusyConnection(migrated(), busy_failures=4)
    manager = SerializedTransactionManager(connection, sleeper=sleeps.append)

    with pytest.raises(ConcurrencyConflictError):
        with manager.unit_of_work():
            pass

    assert connection.begin_attempts == 4
    assert sleeps == [0.025, 0.057, 0.119]
    assert connection.connection.in_transaction is False


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (sqlite3.IntegrityError("UNIQUE constraint failed"), ConstraintViolationError),
        (sqlite3.OperationalError("database is locked"), ConcurrencyConflictError),
        (sqlite3.DatabaseError("database disk image is malformed"), CorruptionDetectedError),
        (sqlite3.OperationalError("disk I/O error"), StorageFailureError),
    ],
)
def test_sqlite_errors_translate_to_canonical_errors(error, expected):
    translated = translate_sqlite_error(error)
    assert isinstance(translated, expected)
    assert isinstance(translated, RepositoryError)
    assert not isinstance(translated, sqlite3.Error)


def test_canonical_error_taxonomy_has_all_twelve_frozen_categories():
    errors = (
        NotFoundError, AlreadyExistsError, ConstraintViolationError, ValidationFailureError,
        ConcurrencyConflictError, StorageFailureError, CorruptionDetectedError,
        RepositoryMigrationFailureError, RepositorySecretUnavailableError,
        BundleMismatchError, VersionIncompatibleError, IdempotencyConflictError,
    )
    assert {error.category for error in errors} == {
        "NOT_FOUND", "ALREADY_EXISTS", "CONSTRAINT_VIOLATION", "VALIDATION_FAILURE",
        "CONCURRENCY_CONFLICT", "STORAGE_FAILURE", "CORRUPTION_DETECTED",
        "MIGRATION_FAILURE", "SECRET_UNAVAILABLE", "BUNDLE_MISMATCH",
        "VERSION_INCOMPATIBLE", "IDEMPOTENCY_CONFLICT",
    }


def test_batch_three_infrastructure_does_not_change_schema():
    connection = migrated()
    before = schema_sha256(connection)
    manager = SerializedTransactionManager(connection)
    with manager.unit_of_work():
        pass
    assert schema_sha256(connection) == before
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 8
