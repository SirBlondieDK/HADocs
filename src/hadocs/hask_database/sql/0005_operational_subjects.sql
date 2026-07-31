CREATE TABLE entity (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    identity_registration_id INTEGER NOT NULL CONSTRAINT uq_entity_registration UNIQUE,
    identity_status TEXT NOT NULL CONSTRAINT ck_entity_identity_status CHECK (identity_status IN ('ACTIVE','RETIRED','IDENTITY_INVALID')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (identity_registration_id) REFERENCES identity_registration(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE entity_current_state (
    id INTEGER PRIMARY KEY CHECK (id>0),
    entity_id INTEGER NOT NULL CONSTRAINT uq_entity_current_state_entity UNIQUE,
    lifecycle_state TEXT NOT NULL CONSTRAINT ck_entity_current_lifecycle CHECK (lifecycle_state IN ('ACTIVE','NOT_OBSERVED','UNAVAILABLE','REMOVED','IDENTITY_INVALID')),
    effective_at TEXT NOT NULL,
    source_event_id INTEGER NOT NULL,
    scan_run_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES entity(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (source_event_id) REFERENCES entity_lifecycle_event(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE relationship (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    public_relationship_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    source_entity_id INTEGER NOT NULL,
    source_ref TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    identity_status TEXT NOT NULL CONSTRAINT ck_relationship_identity_status CHECK (identity_status IN ('ACTIVE','RETIRED','IDENTITY_INVALID')),
    created_at TEXT NOT NULL,
    CONSTRAINT uq_relationship_public UNIQUE (installation_id,public_relationship_id),
    CONSTRAINT uq_relationship_tuple UNIQUE (installation_id,predicate,source_ref,target_ref),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (source_entity_id) REFERENCES entity(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE relationship_current_state (
    id INTEGER PRIMARY KEY CHECK (id>0),
    relationship_id INTEGER NOT NULL CONSTRAINT uq_relationship_current_relationship UNIQUE,
    status TEXT NOT NULL CONSTRAINT ck_relationship_current_status CHECK (status IN ('CURRENT','CURRENT_ABSENT','CAPABILITY_FAIL_CLOSED')),
    predicate TEXT,
    source_ref TEXT,
    target_ref TEXT,
    effective_at TEXT NOT NULL,
    source_event_id INTEGER NOT NULL,
    scan_run_id INTEGER NOT NULL,
    CONSTRAINT ck_relationship_current_tuple CHECK ((status='CURRENT' AND predicate IS NOT NULL AND source_ref IS NOT NULL AND target_ref IS NOT NULL) OR (status IN ('CURRENT_ABSENT','CAPABILITY_FAIL_CLOSED') AND predicate IS NULL AND source_ref IS NULL AND target_ref IS NULL)),
    FOREIGN KEY (relationship_id) REFERENCES relationship(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (source_event_id) REFERENCES relationship_lifecycle_event(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
