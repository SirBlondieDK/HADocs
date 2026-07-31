from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .errors import IntegrityValidationError


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    check: str
    messages: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.messages == ("ok",)


class SQLiteIntegrityValidator:
    """Read-only SQLite integrity checks; never repairs state."""

    @staticmethod
    def _run(connection: sqlite3.Connection, pragma: str) -> IntegrityResult:
        rows = connection.execute(f"PRAGMA {pragma}").fetchall()
        messages = tuple(str(row[0]) for row in rows)
        result = IntegrityResult(pragma, messages)
        if not result.ok:
            raise IntegrityValidationError(f"{pragma} failed")
        return result

    def quick_check(self, connection: sqlite3.Connection) -> IntegrityResult:
        return self._run(connection, "quick_check")

    def integrity_check(self, connection: sqlite3.Connection) -> IntegrityResult:
        return self._run(connection, "integrity_check")

    def startup_verification(self, connection: sqlite3.Connection) -> IntegrityResult:
        return self.quick_check(connection)

    def shutdown_verification(self, connection: sqlite3.Connection) -> IntegrityResult:
        return self.quick_check(connection)
