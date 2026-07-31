from __future__ import annotations

import hashlib
import sqlite3

import pytest

from hadocs.hask_database import (
    FeatureDisabledError,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    LinuxContainerSecretProviderPlaceholder,
    Migration,
    MigrationRegistry,
    MigrationRunner,
    MigrationValidationError,
    NullSecretProvider,
    PragmaValidationError,
    SecretState,
    SecretUnavailableError,
    ServiceState,
    SQLiteIntegrityValidator,
    verify_schema,
)


def enabled_factory(tmp_path):
    return HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=tmp_path / "hask-operational.sqlite")
    )


def test_configuration_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("HADOCS_HASK_DATABASE_ENABLED", raising=False)
    monkeypatch.delenv("HADOCS_HASK_DATABASE_PATH", raising=False)
    assert HaskDatabaseConfig.from_environment() == HaskDatabaseConfig()


def test_disabled_service_does_not_create_database(tmp_path):
    path = tmp_path / "must-not-exist.sqlite"
    service = HaskDatabaseService(HaskSQLiteConnectionFactory(HaskDatabaseConfig(path=path)))
    assert service.startup().state == ServiceState.DISABLED
    assert not path.exists()


def test_disabled_factory_cannot_open_batch_one_database(tmp_path):
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(path=tmp_path / "disabled.sqlite"))
    with pytest.raises(FeatureDisabledError):
        factory.open()


def test_connection_opens_validates_and_closes(tmp_path):
    managed = enabled_factory(tmp_path).open()
    assert managed.connection.execute("SELECT 1").fetchone()[0] == 1
    assert managed.closed is False
    managed.close()
    assert managed.closed is True
    with pytest.raises(sqlite3.ProgrammingError):
        managed.connection.execute("SELECT 1")


def test_required_pragmas_and_wal_are_initialized(tmp_path):
    with enabled_factory(tmp_path).connect() as connection:
        expected = {
            "foreign_keys": 1,
            "journal_mode": "wal",
            "synchronous": 2,
            "busy_timeout": 5000,
            "recursive_triggers": 1,
            "trusted_schema": 0,
            "temp_store": 2,
            "application_id": 0x4841534B,
            "user_version": 0,
        }
        for pragma, value in expected.items():
            actual = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
            if isinstance(value, str):
                actual = str(actual).lower()
            assert actual == value


def test_batch_one_creates_no_schema_objects(tmp_path):
    with enabled_factory(tmp_path).connect() as connection:
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        assert objects == []


def test_wrong_nonzero_application_id_fails_closed(tmp_path):
    path = tmp_path / "not-hask.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA application_id = 123")
    connection.close()
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))
    with pytest.raises(PragmaValidationError, match="application_id"):
        factory.open()


def test_unexpected_user_version_fails_closed(tmp_path):
    path = tmp_path / "future.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA user_version = 1")
    connection.close()
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))
    with pytest.raises(PragmaValidationError, match="user_version"):
        factory.open()


def test_integrity_helpers_return_success_for_empty_database(tmp_path):
    validator = SQLiteIntegrityValidator()
    with enabled_factory(tmp_path).connect() as connection:
        assert validator.quick_check(connection).ok
        assert validator.integrity_check(connection).ok
        assert validator.startup_verification(connection).ok
        assert validator.shutdown_verification(connection).ok


def test_secret_providers_are_safe_nonfunctional_boundaries():
    null = NullSecretProvider()
    linux = LinuxContainerSecretProviderPlaceholder()
    assert null.describe().state == SecretState.ABSENT
    assert linux.describe().state == SecretState.UNAVAILABLE
    for provider in (null, linux):
        with pytest.raises(SecretUnavailableError):
            provider.load("opaque-handle", 1)
        with pytest.raises(SecretUnavailableError):
            provider.create("recovery-set")


def test_migration_registry_is_empty_by_default():
    registry = MigrationRegistry()
    assert registry.migrations == ()
    assert registry.discover(0) == ()


def test_migration_registry_orders_and_verifies_checksums():
    artifact = b"synthetic no-op migration artifact"
    migration = Migration(
        "0001",
        0,
        1,
        artifact,
        hashlib.sha256(artifact).hexdigest(),
        lambda connection: None,
    )
    assert MigrationRegistry((migration,)).discover(0) == (migration,)
    invalid = Migration("0001", 0, 1, artifact, "0" * 64, lambda connection: None)
    with pytest.raises(MigrationValidationError, match="checksum"):
        MigrationRegistry((invalid,))


def test_migration_execution_is_disabled_by_default():
    class VersionStore:
        def current_version(self, connection):
            return 0

        def applied_checksum(self, connection, migration_id):
            return None

        def advance(self, connection, migration):
            raise AssertionError("must not advance")

    with pytest.raises(FeatureDisabledError):
        MigrationRunner().run(sqlite3.connect(":memory:"), VersionStore())


def test_enabled_empty_migration_pipeline_changes_nothing():
    class VersionStore:
        def current_version(self, connection):
            return 0

        def applied_checksum(self, connection, migration_id):
            return None

        def advance(self, connection, migration):
            raise AssertionError("empty registry must not advance")

    connection = sqlite3.connect(":memory:", isolation_level=None)
    assert MigrationRunner(enabled=True).run(connection, VersionStore()) == 0
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
    assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []
    connection.close()


def test_enabled_noop_migration_pipeline_tracks_version_without_schema():
    artifact = b"synthetic no-op migration artifact"
    migration = Migration(
        "0001",
        0,
        1,
        artifact,
        hashlib.sha256(artifact).hexdigest(),
        lambda connection: None,
    )

    class VersionStore:
        version = 0
        checksums = {}

        def current_version(self, connection):
            return self.version

        def applied_checksum(self, connection, migration_id):
            return self.checksums.get(migration_id)

        def advance(self, connection, applied):
            self.version = applied.to_version
            self.checksums[applied.identifier] = applied.expected_sha256

    versions = VersionStore()
    connection = sqlite3.connect(":memory:", isolation_level=None)
    runner = MigrationRunner(MigrationRegistry((migration,)), enabled=True)
    assert runner.run(connection, versions) == 1
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
    assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []
    assert runner.run(connection, versions) == 1
    connection.close()


def test_enabled_service_uses_injected_provider_and_shutdown_verification(tmp_path):
    provider = NullSecretProvider()
    service = HaskDatabaseService(enabled_factory(tmp_path), provider)
    assert service.secret_provider is provider
    assert service.startup().state == ServiceState.ACTIVE
    assert service.shutdown().state == ServiceState.STOPPED


def test_service_migrates_empty_database_and_reopens_version_eight(tmp_path):
    path = tmp_path / "service-owned.sqlite"
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))
    service = HaskDatabaseService(factory)

    assert service.startup().state == ServiceState.ACTIVE
    assert service.shutdown().state == ServiceState.STOPPED

    reconstructed = HaskDatabaseService(factory)
    assert reconstructed.startup().state == ServiceState.ACTIVE
    assert reconstructed.shutdown().state == ServiceState.STOPPED

    strict = HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=path, expected_user_version=8)
    )
    with strict.connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 8
        assert verify_schema(connection).deviations == 0


def test_migration_open_rejects_future_schema_without_weakening_strict_open(tmp_path):
    path = tmp_path / "future-service.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA user_version = 9")
    connection.close()
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))

    with pytest.raises(PragmaValidationError, match="user_version"):
        factory.open_for_migration(8)
    with pytest.raises(PragmaValidationError, match="user_version"):
        factory.open()
