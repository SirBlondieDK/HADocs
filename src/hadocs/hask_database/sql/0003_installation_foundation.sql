CREATE TABLE logical_installation (
    id INTEGER PRIMARY KEY CHECK (id>0),
    state TEXT NOT NULL CONSTRAINT ck_logical_installation_state CHECK (state IN ('ACTIVE','RETIRED')),
    created_at TEXT NOT NULL,
    retired_at TEXT,
    creation_authority TEXT NOT NULL,
    recovery_set_ref TEXT NOT NULL CONSTRAINT uq_logical_installation_recovery UNIQUE,
    current_context_id INTEGER,
    CONSTRAINT ck_logical_installation_retirement CHECK ((state='ACTIVE' AND retired_at IS NULL) OR (state='RETIRED' AND retired_at IS NOT NULL)),
    FOREIGN KEY (current_context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE installation_context (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    predecessor_context_id INTEGER,
    installation_scope TEXT NOT NULL,
    secret_handle TEXT NOT NULL,
    secret_generation INTEGER NOT NULL CONSTRAINT ck_installation_context_generation CHECK (secret_generation>=1),
    format_version INTEGER NOT NULL CONSTRAINT ck_installation_context_format CHECK (format_version>=1),
    status TEXT NOT NULL CONSTRAINT ck_installation_context_status CHECK (status IN ('ACTIVE','SUPERSEDED')),
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    activation_audit_id INTEGER NOT NULL,
    CONSTRAINT uq_installation_context_natural UNIQUE (installation_id,installation_scope,secret_generation,format_version),
    CONSTRAINT ck_installation_context_validity CHECK ((status='ACTIVE' AND valid_until IS NULL) OR (status='SUPERSEDED' AND valid_until IS NOT NULL)),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (predecessor_context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (activation_audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE authoritative_declaration (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    declaration_key TEXT NOT NULL,
    declaration_version INTEGER NOT NULL CONSTRAINT ck_authoritative_declaration_version CHECK (declaration_version>=1),
    protected_content_ref TEXT NOT NULL,
    authority_status TEXT NOT NULL CONSTRAINT ck_authoritative_declaration_authority CHECK (authority_status IN ('AUTHORITATIVE','REVOKED')),
    integrity_status TEXT NOT NULL CONSTRAINT ck_authoritative_declaration_integrity CHECK (integrity_status IN ('VALID','INVALID','UNKNOWN')),
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    CONSTRAINT uq_authoritative_declaration_version UNIQUE (installation_id,declaration_key,declaration_version),
    CONSTRAINT ck_authoritative_declaration_validity CHECK ((authority_status='AUTHORITATIVE' AND valid_until IS NULL) OR (authority_status='REVOKED' AND valid_until IS NOT NULL)),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE protected_provenance_reference (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    provider_ref TEXT NOT NULL,
    provider_version TEXT NOT NULL,
    integrity_status TEXT NOT NULL CONSTRAINT ck_provenance_integrity CHECK (integrity_status IN ('VALID','INVALID','UNKNOWN')),
    availability_status TEXT NOT NULL CONSTRAINT ck_provenance_availability CHECK (availability_status IN ('AVAILABLE','UNAVAILABLE')),
    created_at TEXT NOT NULL,
    CONSTRAINT uq_provenance_provider UNIQUE (installation_id,provider_ref,provider_version),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
