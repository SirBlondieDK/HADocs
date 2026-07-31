from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from .config import HaskDatabaseConfig
from .errors import FeatureDisabledError, PragmaValidationError
from .integrity import SQLiteIntegrityValidator

HASK_APPLICATION_ID = 0x4841534B


def _pragma_value(connection: sqlite3.Connection, name: str) -> object:
    row = connection.execute(f"PRAGMA {name}").fetchone()
    if row is None:
        raise PragmaValidationError(f"PRAGMA {name} returned no value")
    return row[0]


class ManagedSQLiteConnection:
    """Explicit open/close lifecycle with fail-closed integrity validation."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        integrity: SQLiteIntegrityValidator,
    ) -> None:
        self.connection = connection
        self._integrity = integrity
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self, *, verify: bool = True) -> None:
        if self._closed:
            return
        try:
            if verify:
                self._integrity.shutdown_verification(self.connection)
        finally:
            self.connection.close()
            self._closed = True

    def __enter__(self) -> sqlite3.Connection:
        return self.connection

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close(verify=exc_type is None)


class HaskSQLiteConnectionFactory:
    """Creates validated connections to the separate HASK SQLite file."""

    def __init__(
        self,
        config: HaskDatabaseConfig | None = None,
        integrity: SQLiteIntegrityValidator | None = None,
    ) -> None:
        self.config = config or HaskDatabaseConfig()
        self.integrity = integrity or SQLiteIntegrityValidator()

    def open(self) -> ManagedSQLiteConnection:
        return self._open(frozenset({self.config.expected_user_version}))

    def open_for_migration(self, target_user_version: int) -> ManagedSQLiteConnection:
        """Open a known schema version for immediate forward migration.

        Normal ``open`` remains strict.  This deliberately bounded path admits
        only versions in the packaged forward chain and is used by the service
        before it migrates and verifies the connection.
        """

        if target_user_version < 0:
            raise ValueError("target_user_version must be non-negative")
        return self._open(frozenset(range(target_user_version + 1)))

    def _open(self, allowed_user_versions: frozenset[int]) -> ManagedSQLiteConnection:
        if not self.config.enabled:
            raise FeatureDisabledError("HASK database infrastructure is disabled")
        assert self.config.path is not None
        path = Path(self.config.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path,
            timeout=self.config.busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        try:
            self._initialize_pragmas(connection)
            self._validate_pragmas(connection, allowed_user_versions)
            self.integrity.startup_verification(connection)
        except Exception:
            connection.close()
            raise
        return ManagedSQLiteConnection(connection, self.integrity)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        managed = self.open()
        try:
            yield managed.connection
        except Exception:
            managed.close(verify=False)
            raise
        else:
            managed.close()

    def _initialize_pragmas(self, connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        journal_mode = str(_pragma_value_after(connection, "journal_mode", "WAL")).lower()
        if journal_mode != "wal":
            raise PragmaValidationError("journal_mode WAL could not be initialized")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute(f"PRAGMA busy_timeout = {self.config.busy_timeout_ms}")
        connection.execute("PRAGMA recursive_triggers = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
        connection.execute("PRAGMA temp_store = MEMORY")
        connection.execute("PRAGMA wal_autocheckpoint = 1000")

        application_id = int(_pragma_value(connection, "application_id"))
        if application_id == 0:
            connection.execute(f"PRAGMA application_id = {HASK_APPLICATION_ID}")
        elif application_id != HASK_APPLICATION_ID:
            raise PragmaValidationError("database has an unexpected nonzero application_id")

    def _validate_pragmas(
        self,
        connection: sqlite3.Connection,
        allowed_user_versions: frozenset[int],
    ) -> None:
        expected = {
            "foreign_keys": 1,
            "journal_mode": "wal",
            "synchronous": 2,
            "busy_timeout": self.config.busy_timeout_ms,
            "recursive_triggers": 1,
            "trusted_schema": 0,
            "temp_store": 2,
            "application_id": HASK_APPLICATION_ID,
        }
        for name, required in expected.items():
            actual = _pragma_value(connection, name)
            if isinstance(required, str):
                actual = str(actual).lower()
            if actual != required:
                raise PragmaValidationError(
                    f"PRAGMA {name} validation failed: expected {required!r}, got {actual!r}"
                )
        user_version = int(_pragma_value(connection, "user_version"))
        if user_version not in allowed_user_versions:
            expected_versions = ", ".join(str(item) for item in sorted(allowed_user_versions))
            raise PragmaValidationError(
                "PRAGMA user_version validation failed: "
                f"expected one of {{{expected_versions}}}, got {user_version!r}"
            )


def _pragma_value_after(
    connection: sqlite3.Connection,
    name: str,
    value: str,
) -> object:
    row = connection.execute(f"PRAGMA {name} = {value}").fetchone()
    if row is None:
        raise PragmaValidationError(f"PRAGMA {name} returned no value")
    return row[0]
