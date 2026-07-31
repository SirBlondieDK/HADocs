from __future__ import annotations

import hashlib
import sqlite3

import pytest

from hadocs.hask_database import (
    BATCH2_MIGRATIONS,
    BATCH2_REGISTRY,
    HaskDatabaseConfig,
    HaskSQLiteConnectionFactory,
    Migration,
    MigrationRegistry,
    MigrationValidationError,
    initialize_batch2_schema,
    schema_sha256,
    verify_schema,
)


def migrated() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    assert initialize_batch2_schema(connection) == 8
    return connection


def test_frozen_eight_phase_chain_is_ordered_and_checksummed():
    assert [item.identifier for item in BATCH2_MIGRATIONS] == [f"{n:04d}" for n in range(1, 9)]
    assert [(item.from_version, item.to_version) for item in BATCH2_MIGRATIONS] == [
        (n - 1, n) for n in range(1, 9)
    ]
    for item in BATCH2_MIGRATIONS:
        assert hashlib.sha256(item.artifact).hexdigest() == item.expected_sha256


def test_schema_conforms_to_all_frozen_inventory_counts():
    connection = migrated()
    result = verify_schema(connection)
    assert result.deviations == 0
    assert (result.tables, result.columns, result.primary_keys) == (25, 243, 25)
    assert (result.alternate_keys, result.foreign_keys) == (28, 57)
    assert (result.logical_constraints, result.indexes) == (30, 18)
    assert (result.trigger_contracts, result.views, result.migrations) == (7, 1, 8)
    assert result.lifecycle_history_columns == 14


def test_db002a_audit_evidence_resolution_is_exact():
    connection = migrated()
    unique_columns = {
        tuple(row[2] for row in connection.execute(f'PRAGMA index_info("{index[1]}")'))
        for index in connection.execute('PRAGMA index_list("audit_evidence_link")')
        if index[2]
    }
    assert ("audit_id", "observation_id", "role") in unique_columns
    assert ("audit_id", "ordinal") not in unique_columns
    table_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE name='audit_evidence_link'"
    ).fetchone()[0]
    assert "check(ordinal>=0)" in "".join(table_sql.lower().split())


def test_negative_audit_ordinal_is_rejected_without_transaction_semantics():
    connection = migrated()
    connection.execute("PRAGMA foreign_keys=OFF")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
        connection.execute(
            "INSERT INTO audit_evidence_link VALUES (?, ?, ?, ?, ?)",
            (1, 1, 1, "PRIMARY", -1),
        )


def test_lifecycle_history_is_a_read_only_view():
    connection = migrated()
    assert connection.execute(
        "SELECT type FROM sqlite_master WHERE name='lifecycle_history'"
    ).fetchone()[0] == "view"
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("DELETE FROM lifecycle_history")


def test_migration_replay_is_idempotent():
    connection = migrated()
    before = schema_sha256(connection)
    assert initialize_batch2_schema(connection) == 8
    assert schema_sha256(connection) == before


def test_migration_artifact_checksum_tampering_fails_closed():
    original = BATCH2_MIGRATIONS[0]
    tampered = Migration(
        original.identifier,
        original.from_version,
        original.to_version,
        original.artifact + b" ",
        original.expected_sha256,
        original.operation,
    )
    with pytest.raises(MigrationValidationError, match="checksum"):
        MigrationRegistry((tampered,))


def test_schema_generation_is_deterministic():
    first, second = migrated(), migrated()
    assert schema_sha256(first) == schema_sha256(second)


def test_integrity_checks_and_schema_version_pass():
    connection = migrated()
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 8
    assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_file_database_initialization_preserves_batch_one_pragmas(tmp_path):
    path = tmp_path / "batch2.sqlite"
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))
    with factory.connect() as connection:
        assert initialize_batch2_schema(connection) == 8
        assert connection.execute("PRAGMA application_id").fetchone()[0] == 0x4841534B
    reopened = HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=path, expected_user_version=8)
    )
    with reopened.connect() as connection:
        assert verify_schema(connection).deviations == 0


def test_all_seven_trigger_contracts_are_materialized():
    connection = migrated()
    sql = "\n".join(
        row[0] for row in connection.execute("SELECT sql FROM sqlite_master WHERE type='trigger'")
    )
    for number in range(1, 8):
        assert f"DB002-TR-{number:03d}" in sql
