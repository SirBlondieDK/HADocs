from __future__ import annotations

from pathlib import Path
import sqlite3

from .migrations import Migration, MigrationRegistry, MigrationRunner, SchemaVersionStore

_SQL_DIR = Path(__file__).with_name("sql")
_CHECKSUMS = {
    "0001": "b0545489362616656e213355a67dfb068a6248df2a22a934b1131f066b11d18f",
    "0002": "f15ad8763775afeb74b90e4bb2f2e97d3a8192de41555c990aa970bddf822a3e",
    "0003": "179746c519575d409ed967c90f2df555e235ce048d9aaa29f1fd981d7d0d76b5",
    "0004": "25883b5cfac523822c85f7116760c39cd91bc4dea55fac5e941d489e5ddca9bd",
    "0005": "b3a9db44f2b28e4f4a44c15673c945d0a9b272d39ba0f2f09b1a79ca34524f32",
    "0006": "de29214ce070666ad4a9d864b028b7de409228c68b9f17f293f84a738c75978e",
    "0007": "7c025865f04416e926a88d7df7f02eaedae2df4d0e20bdb545c6b7ee1acb11f6",
    "0008": "a0dfe2a67d2258abc3a4cede53a27feae3a97f638ec51eaf2b14d273dee1ef2f",
}


def _execute_artifact(artifact: bytes):
    text = artifact.decode("utf-8")

    def operation(connection: sqlite3.Connection) -> None:
        statement = ""
        for line in text.splitlines(keepends=True):
            statement += line
            if sqlite3.complete_statement(statement):
                if statement.strip():
                    connection.execute(statement)
                statement = ""
        if statement.strip():
            raise sqlite3.OperationalError("incomplete migration SQL")

    return operation


def _build_migrations() -> tuple[Migration, ...]:
    migrations: list[Migration] = []
    for version in range(1, 9):
        identifier = f"{version:04d}"
        path = next(_SQL_DIR.glob(f"{identifier}_*.sql"))
        artifact = path.read_bytes()
        migrations.append(
            Migration(
                identifier=identifier,
                from_version=version - 1,
                to_version=version,
                artifact=artifact,
                expected_sha256=_CHECKSUMS[identifier],
                operation=_execute_artifact(artifact),
            )
        )
    return tuple(migrations)


class PragmaSchemaVersionStore(SchemaVersionStore):
    """Version/checksum adapter for the immutable packaged migration chain."""

    def current_version(self, connection: sqlite3.Connection) -> int:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])

    def applied_checksum(self, connection: sqlite3.Connection, migration_id: str) -> str | None:
        current = self.current_version(connection)
        return _CHECKSUMS[migration_id] if int(migration_id) <= current else None

    def advance(self, connection: sqlite3.Connection, migration: Migration) -> None:
        if migration.from_version != self.current_version(connection):
            raise sqlite3.IntegrityError("schema version changed during migration")


BATCH2_MIGRATIONS = _build_migrations()
BATCH2_REGISTRY = MigrationRegistry(BATCH2_MIGRATIONS)


def initialize_batch2_schema(connection: sqlite3.Connection) -> int:
    """Apply the frozen eight-phase schema chain to an enabled connection."""

    return MigrationRunner(BATCH2_REGISTRY, enabled=True).run(
        connection, PragmaSchemaVersionStore()
    )
