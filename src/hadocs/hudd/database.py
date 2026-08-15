from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PACKAGE_DIR / "data" / "hudd.sqlite"


def database_path() -> Path:
    """Return the configured HUDD database path."""
    configured = os.getenv("HUDD_DATABASE_PATH")
    if not configured:
        return DEFAULT_DATABASE_PATH
    from hadocs.platform.paths import AppPaths

    return AppPaths.discover().resolve_resource_path(configured)


def connect(path: str | Path | None = None, *, read_only: bool = False) -> sqlite3.Connection:
    db_path = Path(path) if path else database_path()
    if not db_path.exists():
        raise FileNotFoundError(f"HUDD database not found: {db_path}")
    if read_only:
        connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection(path: str | Path | None = None, *, read_only: bool = True) -> Iterator[sqlite3.Connection]:
    con = connect(path, read_only=read_only)
    try:
        yield con
    finally:
        con.close()
