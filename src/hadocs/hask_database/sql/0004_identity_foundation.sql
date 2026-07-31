CREATE TABLE collision_registry (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL CONSTRAINT uq_collision_registry_installation UNIQUE,
    integrity_status TEXT NOT NULL CONSTRAINT ck_collision_registry_integrity CHECK (integrity_status IN ('VALID','INVALID','UNKNOWN')),
    availability_status TEXT NOT NULL CONSTRAINT ck_collision_registry_availability CHECK (availability_status IN ('AVAILABLE','UNAVAILABLE')),
    format_version INTEGER NOT NULL CONSTRAINT ck_collision_registry_format CHECK (format_version>=1),
    created_at TEXT NOT NULL,
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE identity_registration (
    id INTEGER PRIMARY KEY CHECK (id>0),
    registry_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    reference_kind TEXT NOT NULL CONSTRAINT ck_identity_registration_kind CHECK (reference_kind IN ('entity','device','area','label')),
    format_version INTEGER NOT NULL CONSTRAINT ck_identity_registration_format CHECK (format_version>=1),
    canonical_tuple_handle TEXT NOT NULL,
    opaque_reference TEXT NOT NULL,
    secret_generation INTEGER NOT NULL CONSTRAINT ck_identity_registration_generation CHECK (secret_generation>=1),
    status TEXT NOT NULL CONSTRAINT ck_identity_registration_status CHECK (status IN ('ACTIVE','RETIRED','IDENTITY_INVALID')),
    registered_at TEXT NOT NULL,
    retired_at TEXT,
    registration_audit_id INTEGER NOT NULL,
    identity_digest BLOB NOT NULL CONSTRAINT ck_identity_registration_digest CHECK (length(identity_digest)=32),
    CONSTRAINT uq_identity_registration_private UNIQUE (registry_id,context_id,reference_kind,format_version,canonical_tuple_handle,secret_generation),
    CONSTRAINT uq_identity_registration_opaque UNIQUE (registry_id,context_id,reference_kind,format_version,opaque_reference),
    CONSTRAINT ck_identity_registration_retirement CHECK ((status='ACTIVE' AND retired_at IS NULL) OR (status='RETIRED' AND retired_at IS NOT NULL) OR (status='IDENTITY_INVALID' AND retired_at IS NULL)),
    FOREIGN KEY (registry_id) REFERENCES collision_registry(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (registration_audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
