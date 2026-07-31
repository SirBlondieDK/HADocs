from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import sqlite3
from typing import Callable, Protocol

from .errors import FeatureDisabledError, MigrationValidationError
from .integrity import SQLiteIntegrityValidator

_MIGRATION_ID = re.compile(r"^[0-9]{4}$")


class SchemaVersionStore(Protocol):
    """Future authoritative schema-version storage boundary."""

    def current_version(self, connection: sqlite3.Connection) -> int: ...

    def applied_checksum(
        self, connection: sqlite3.Connection, migration_id: str
    ) -> str | None: ...

    def advance(self, connection: sqlite3.Connection, migration: Migration) -> None: ...


MigrationOperation = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True, slots=True)
class Migration:
    identifier: str
    from_version: int
    to_version: int
    artifact: bytes
    expected_sha256: str
    operation: MigrationOperation

    def validate(self) -> None:
        if not _MIGRATION_ID.fullmatch(self.identifier):
            raise MigrationValidationError("migration ID must be four decimal digits")
        if self.from_version < 0 or self.to_version != self.from_version + 1:
            raise MigrationValidationError("migration versions must advance exactly once")
        if not re.fullmatch(r"[0-9a-f]{64}", self.expected_sha256):
            raise MigrationValidationError("migration checksum must be lowercase SHA-256")
        actual = hashlib.sha256(self.artifact).hexdigest()
        if actual != self.expected_sha256:
            raise MigrationValidationError("migration checksum mismatch")


class MigrationRegistry:
    """Validated, ordered registry of immutable migration artifacts."""

    def __init__(self, migrations: tuple[Migration, ...] = ()) -> None:
        ordered = tuple(sorted(migrations, key=lambda item: item.identifier))
        seen: set[str] = set()
        previous: Migration | None = None
        for migration in ordered:
            migration.validate()
            if migration.identifier in seen:
                raise MigrationValidationError("duplicate migration ID")
            if previous is None:
                if migration.identifier != "0001" or migration.from_version != 0:
                    raise MigrationValidationError("migration chain must begin at 0001/version 0")
            elif (
                migration.from_version != previous.to_version
                or int(migration.identifier) != int(previous.identifier) + 1
            ):
                raise MigrationValidationError("migration chain contains an ID or version gap")
            seen.add(migration.identifier)
            previous = migration
        self._migrations = ordered

    @property
    def migrations(self) -> tuple[Migration, ...]:
        return self._migrations

    def discover(self, current_version: int) -> tuple[Migration, ...]:
        candidates = tuple(
            migration for migration in self._migrations if migration.from_version >= current_version
        )
        if candidates and candidates[0].from_version != current_version:
            raise MigrationValidationError("no migration starts at the current schema version")
        return candidates


class MigrationRunner:
    """Ordered, checksummed, forward-only migration pipeline."""

    def __init__(
        self,
        registry: MigrationRegistry | None = None,
        *,
        enabled: bool = False,
        integrity: SQLiteIntegrityValidator | None = None,
    ) -> None:
        self.registry = registry or MigrationRegistry()
        self.enabled = enabled
        self.integrity = integrity or SQLiteIntegrityValidator()

    def run(self, connection: sqlite3.Connection, versions: SchemaVersionStore) -> int:
        if not self.enabled:
            raise FeatureDisabledError("migration execution is disabled")
        self.integrity.integrity_check(connection)
        current = versions.current_version(connection)
        for migration in self.registry.migrations:
            if migration.to_version > current:
                break
            recorded = versions.applied_checksum(connection, migration.identifier)
            if recorded != migration.expected_sha256:
                raise MigrationValidationError("applied migration checksum mismatch")
        for migration in self.registry.discover(current):
            migration.validate()
            if migration.from_version != current:
                raise MigrationValidationError("migration order does not match current version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                migration.operation(connection)
                versions.advance(connection, migration)
                connection.execute(f"PRAGMA user_version = {migration.to_version}")
                self.integrity.integrity_check(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            current = migration.to_version
        return current
