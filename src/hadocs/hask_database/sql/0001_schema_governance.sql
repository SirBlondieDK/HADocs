CREATE TABLE migration_state (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    singleton_key INTEGER NOT NULL DEFAULT 1 CONSTRAINT uq_migration_state_singleton UNIQUE CONSTRAINT ck_migration_state_singleton CHECK (singleton_key = 1),
    current_schema_version INTEGER NOT NULL CONSTRAINT ck_migration_state_version CHECK (current_schema_version >= 0),
    status TEXT NOT NULL CONSTRAINT ck_migration_state_status CHECK (status IN ('IDLE','RUNNING','BLOCKED')),
    active_attempt_id INTEGER,
    recovery_set_ref TEXT NOT NULL,
    validation_status TEXT NOT NULL CONSTRAINT ck_migration_state_validation CHECK (validation_status IN ('PENDING','VALID','INVALID','UNAVAILABLE')),
    updated_at TEXT NOT NULL,
    CONSTRAINT ck_migration_state_combination CHECK (
        (status='IDLE' AND active_attempt_id IS NULL AND validation_status='VALID') OR
        (status='RUNNING' AND active_attempt_id IS NOT NULL AND validation_status='PENDING') OR
        (status='BLOCKED' AND active_attempt_id IS NOT NULL AND validation_status IN ('INVALID','UNAVAILABLE'))
    ),
    FOREIGN KEY (active_attempt_id) REFERENCES migration_attempt(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE migration_attempt (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    migration_state_id INTEGER NOT NULL,
    migration_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    from_version INTEGER NOT NULL CONSTRAINT ck_migration_attempt_from CHECK (from_version >= 0),
    to_version INTEGER NOT NULL CONSTRAINT ck_migration_attempt_to CHECK (to_version = from_version + 1),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CONSTRAINT ck_migration_attempt_status CHECK (status IN ('PLANNED','RUNNING','SUCCEEDED','FAILED','INTERRUPTED')),
    recovery_set_validation TEXT NOT NULL CONSTRAINT ck_migration_attempt_recovery CHECK (recovery_set_validation IN ('NOT_REQUIRED','VALID','INVALID','UNAVAILABLE')),
    safe_error_code TEXT,
    audit_id INTEGER,
    migration_checksum BLOB NOT NULL CONSTRAINT ck_migration_attempt_checksum CHECK (length(migration_checksum)=32),
    CONSTRAINT uq_migration_attempt_id UNIQUE (migration_state_id,migration_id),
    CONSTRAINT uq_migration_attempt_idempotency UNIQUE (migration_state_id,idempotency_key),
    CONSTRAINT ck_migration_attempt_combination CHECK (
        (status IN ('PLANNED','RUNNING') AND finished_at IS NULL AND safe_error_code IS NULL AND audit_id IS NULL AND recovery_set_validation IN ('VALID','NOT_REQUIRED')) OR
        (status='SUCCEEDED' AND finished_at IS NOT NULL AND safe_error_code IS NULL AND audit_id IS NOT NULL AND recovery_set_validation IN ('VALID','NOT_REQUIRED')) OR
        (status IN ('FAILED','INTERRUPTED') AND finished_at IS NOT NULL AND safe_error_code IS NOT NULL AND audit_id IS NOT NULL)
    ),
    FOREIGN KEY (migration_state_id) REFERENCES migration_state(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
