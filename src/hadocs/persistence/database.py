from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS policies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        enabled INTEGER NOT NULL,
        priority INTEGER NOT NULL,
        scope_json TEXT NOT NULL,
        action_json TEXT NOT NULL,
        reason TEXT NOT NULL,
        starts_at TEXT,
        expires_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS scan_runs (
        id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        raw_finding_count INTEGER NOT NULL DEFAULT 0,
        effective_finding_count INTEGER NOT NULL DEFAULT 0,
        health_score REAL,
        error TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS findings (
        id TEXT PRIMARY KEY,
        scan_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scan_runs(id) ON DELETE CASCADE
    )''',
    '''CREATE TABLE IF NOT EXISTS score_snapshots (
        scan_id TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scan_runs(id) ON DELETE CASCADE
    )''',
    '''CREATE TABLE IF NOT EXISTS policy_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        before_json TEXT,
        after_json TEXT,
        created_at TEXT NOT NULL
    )''',
]

def default_database_path() -> Path:
    explicit = os.environ.get('HADOCS_DATABASE_FILE')
    if explicit:
        return Path(explicit).expanduser().resolve()
    config = os.environ.get('HADOCS_CONFIG_FILE')
    if config:
        return Path(config).expanduser().resolve().parent / 'hadocs.db'
    return Path('config/hadocs.db').resolve()

class Database:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or default_database_path()).resolve()

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        connection.execute('PRAGMA journal_mode = WAL')
        connection.execute('PRAGMA busy_timeout = 5000')
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            for statement in SCHEMA:
                connection.execute(statement)
            connection.execute(
                'CREATE INDEX IF NOT EXISTS idx_policy_priority ON policies(enabled, priority)'
            )
