CREATE TABLE version_state (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    singleton_key INTEGER NOT NULL DEFAULT 1 CONSTRAINT uq_version_state_singleton UNIQUE CONSTRAINT ck_version_state_singleton CHECK (singleton_key=1),
    schema_version INTEGER NOT NULL CONSTRAINT ck_version_state_schema CHECK (schema_version>=0),
    architecture_version TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    implementation_version TEXT NOT NULL,
    hask_bundle_ref TEXT NOT NULL,
    hask_bundle_version TEXT NOT NULL,
    hask_bundle_digest BLOB NOT NULL CONSTRAINT ck_version_state_digest CHECK (length(hask_bundle_digest)=32),
    hask_compatibility_status TEXT NOT NULL CONSTRAINT ck_version_state_compatibility CHECK (hask_compatibility_status IN ('COMPATIBLE','CONDITIONALLY_COMPATIBLE','INCOMPATIBLE','UNKNOWN')),
    hask_activated_at TEXT,
    previous_hask_bundle_ref TEXT,
    rollback_hask_bundle_ref TEXT,
    hudd_ref TEXT NOT NULL,
    validation_status TEXT NOT NULL CONSTRAINT ck_version_state_validation CHECK (validation_status IN ('PENDING','VALID','INVALID','UNAVAILABLE')),
    CONSTRAINT ck_version_state_activation CHECK (hask_activated_at IS NOT NULL OR (previous_hask_bundle_ref IS NULL AND rollback_hask_bundle_ref IS NULL))
);
