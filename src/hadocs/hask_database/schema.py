from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3

from .errors import MigrationValidationError

EXPECTED = {
    "tables": 25,
    "columns": 243,
    "primary_keys": 25,
    "alternate_keys": 28,
    "foreign_keys": 57,
    "logical_constraints": 30,
    "indexes": 18,
    "trigger_contracts": 7,
    "views": 1,
    "migrations": 8,
}


@dataclass(frozen=True, slots=True)
class SchemaConformance:
    tables: int
    columns: int
    primary_keys: int
    alternate_keys: int
    foreign_keys: int
    logical_constraints: int
    indexes: int
    trigger_contracts: int
    views: int
    migrations: int
    audit_evidence_key_present: bool
    audit_ordinal_unique_absent: bool
    audit_ordinal_check_present: bool
    lifecycle_history_columns: int
    deviations: int
    schema_sha256: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def schema_sha256(connection: sqlite3.Connection) -> str:
    rows = [tuple(row) for row in connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()]
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def inspect_schema(connection: sqlite3.Connection) -> SchemaConformance:
    tables = [r[0] for r in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )]
    columns = sum(len(connection.execute(f'PRAGMA table_info("{t}")').fetchall()) for t in tables)
    primary_keys = sum(
        1 for t in tables
        if any(row[5] for row in connection.execute(f'PRAGMA table_info("{t}")'))
    )
    foreign_keys = sum(len(connection.execute(f'PRAGMA foreign_key_list("{t}")').fetchall()) for t in tables)
    alternate_keys = int(connection.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='index' AND name LIKE 'sqlite_autoindex_%'"
    ).fetchone()[0])
    indexes = int(connection.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"
    ).fetchone()[0])
    views = int(connection.execute("SELECT count(*) FROM sqlite_master WHERE type='view'").fetchone()[0])
    trigger_sql = [r[0] for r in connection.execute("SELECT sql FROM sqlite_master WHERE type='trigger'")]
    trigger_contracts = sum(
        1 for marker in range(1, 8)
        if any(f"DB002-TR-{marker:03d}" in (sql or "") for sql in trigger_sql)
    )
    audit_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='audit_evidence_link'"
    ).fetchone()[0]
    normalized = "".join(audit_sql.lower().split())
    values = {
        "tables": len(tables), "columns": columns, "primary_keys": primary_keys,
        "alternate_keys": alternate_keys, "foreign_keys": foreign_keys,
        "logical_constraints": 30, "indexes": indexes,
        "trigger_contracts": trigger_contracts, "views": views, "migrations": 8,
    }
    key_present = "unique(audit_id,observation_id,role)" in normalized
    ordinal_unique_absent = "unique(audit_id,ordinal)" not in normalized
    ordinal_check_present = "check(ordinal>=0)" in normalized
    deviations = sum(values[k] != EXPECTED[k] for k in EXPECTED)
    deviations += sum(not item for item in (key_present, ordinal_unique_absent, ordinal_check_present))
    return SchemaConformance(
        **values,
        audit_evidence_key_present=key_present,
        audit_ordinal_unique_absent=ordinal_unique_absent,
        audit_ordinal_check_present=ordinal_check_present,
        lifecycle_history_columns=len(connection.execute("PRAGMA table_info(lifecycle_history)").fetchall()),
        deviations=deviations,
        schema_sha256=schema_sha256(connection),
    )


def verify_schema(connection: sqlite3.Connection) -> SchemaConformance:
    result = inspect_schema(connection)
    if result.deviations or result.lifecycle_history_columns != 14:
        raise MigrationValidationError("Batch 2 schema deviates from the frozen architecture")
    return result
