CREATE TABLE entity_lifecycle_event (
    id INTEGER PRIMARY KEY CHECK (id>0),
    entity_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    prior_state TEXT CONSTRAINT ck_entity_event_prior CHECK (prior_state IS NULL OR prior_state IN ('ACTIVE','NOT_OBSERVED','UNAVAILABLE','REMOVED','IDENTITY_INVALID')),
    result_state TEXT NOT NULL CONSTRAINT ck_entity_event_result CHECK (result_state IN ('ACTIVE','NOT_OBSERVED','UNAVAILABLE','REMOVED','IDENTITY_INVALID')),
    observation_id INTEGER NOT NULL,
    scan_run_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,
    event_at TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    CONSTRAINT uq_entity_event_idempotency UNIQUE (entity_id,idempotency_key),
    FOREIGN KEY (entity_id) REFERENCES entity(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (observation_id) REFERENCES observation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE relationship_lifecycle_event (
    id INTEGER PRIMARY KEY CHECK (id>0),
    relationship_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    event_kind TEXT NOT NULL CONSTRAINT ck_relationship_event_kind CHECK (event_kind IN ('CREATED','REPLACED','REMOVED','RECREATED')),
    prior_predicate TEXT,
    prior_source_ref TEXT,
    prior_target_ref TEXT,
    result_predicate TEXT,
    result_source_ref TEXT,
    result_target_ref TEXT,
    continuity TEXT NOT NULL CONSTRAINT ck_relationship_continuity CHECK (continuity IN ('PRESERVED','DISCONTINUOUS','UNKNOWN')),
    observation_id INTEGER NOT NULL,
    scan_run_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,
    event_at TEXT NOT NULL,
    CONSTRAINT uq_relationship_event_idempotency UNIQUE (relationship_id,idempotency_key),
    CONSTRAINT ck_relationship_event_tuple CHECK (
        (event_kind IN ('CREATED','RECREATED') AND prior_predicate IS NULL AND prior_source_ref IS NULL AND prior_target_ref IS NULL AND result_predicate IS NOT NULL AND result_source_ref IS NOT NULL AND result_target_ref IS NOT NULL) OR
        (event_kind='REPLACED' AND prior_predicate IS NOT NULL AND prior_source_ref IS NOT NULL AND prior_target_ref IS NOT NULL AND result_predicate IS NOT NULL AND result_source_ref IS NOT NULL AND result_target_ref IS NOT NULL) OR
        (event_kind='REMOVED' AND prior_predicate IS NOT NULL AND prior_source_ref IS NOT NULL AND prior_target_ref IS NOT NULL AND result_predicate IS NULL AND result_source_ref IS NULL AND result_target_ref IS NULL)
    ),
    FOREIGN KEY (relationship_id) REFERENCES relationship(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (observation_id) REFERENCES observation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE clone_decision (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    declaration_id INTEGER,
    provenance_reference_id INTEGER NOT NULL,
    classification TEXT NOT NULL CONSTRAINT ck_clone_classification CHECK (classification IN ('SAME_LOGICAL_INSTALLATION','DISTINCT_LOGICAL_INSTALLATION','UNKNOWN')),
    ambiguity_state TEXT NOT NULL CONSTRAINT ck_clone_ambiguity CHECK (ambiguity_state IN ('RESOLVED','UNRESOLVED')),
    activation_outcome TEXT NOT NULL CONSTRAINT ck_clone_activation CHECK (activation_outcome IN ('PRESERVE_CONTEXT','NEW_CONTEXT_REQUIRED','FAIL_CLOSED')),
    decided_at TEXT NOT NULL,
    decision_digest BLOB NOT NULL CONSTRAINT ck_clone_digest CHECK (length(decision_digest)=32),
    audit_id INTEGER NOT NULL,
    CONSTRAINT uq_clone_decision_idempotency UNIQUE (installation_id,idempotency_key),
    CONSTRAINT ck_clone_combination CHECK (
        (classification='SAME_LOGICAL_INSTALLATION' AND ambiguity_state='RESOLVED' AND activation_outcome IN ('PRESERVE_CONTEXT','FAIL_CLOSED')) OR
        (classification='DISTINCT_LOGICAL_INSTALLATION' AND ambiguity_state='RESOLVED' AND activation_outcome='NEW_CONTEXT_REQUIRED') OR
        (classification='UNKNOWN' AND ambiguity_state='UNRESOLVED' AND activation_outcome='FAIL_CLOSED')
    ),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (declaration_id) REFERENCES authoritative_declaration(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (provenance_reference_id) REFERENCES protected_provenance_reference(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE compatibility_decision (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER,
    scan_run_id INTEGER,
    idempotency_key TEXT NOT NULL,
    version_vector_json TEXT NOT NULL CONSTRAINT ck_compatibility_version_json CHECK (json_valid(version_vector_json)=1 AND json_type(version_vector_json)='object'),
    result TEXT NOT NULL CONSTRAINT ck_compatibility_result CHECK (result IN ('COMPATIBLE','CONDITIONALLY_COMPATIBLE','INCOMPATIBLE','UNKNOWN')),
    capability_outcome TEXT NOT NULL CONSTRAINT ck_compatibility_outcome CHECK (capability_outcome IN ('CAPABILITY_ENABLED','CAPABILITY_LIMITED','CAPABILITY_FAIL_CLOSED')),
    decided_at TEXT NOT NULL,
    decision_digest BLOB NOT NULL CONSTRAINT ck_compatibility_digest CHECK (length(decision_digest)=32),
    audit_id INTEGER NOT NULL,
    safe_failure_code TEXT,
    CONSTRAINT uq_compatibility_idempotency UNIQUE (installation_id,context_id,idempotency_key),
    CONSTRAINT ck_compatibility_combination CHECK (
        (result='COMPATIBLE' AND capability_outcome='CAPABILITY_ENABLED') OR
        (result='CONDITIONALLY_COMPATIBLE' AND capability_outcome='CAPABILITY_LIMITED') OR
        (result IN ('INCOMPATIBLE','UNKNOWN') AND capability_outcome='CAPABILITY_FAIL_CLOSED')
    ),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE activation_outcome (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    clone_decision_id INTEGER NOT NULL,
    compatibility_decision_id INTEGER NOT NULL,
    secret_validation TEXT NOT NULL CONSTRAINT ck_activation_secret CHECK (secret_validation IN ('VALID','INVALID','UNAVAILABLE')),
    provenance_validation TEXT NOT NULL CONSTRAINT ck_activation_provenance CHECK (provenance_validation IN ('VALID','INVALID','UNAVAILABLE')),
    requested_state TEXT NOT NULL CONSTRAINT ck_activation_requested CHECK (requested_state IN ('ACTIVE','INACTIVE')),
    result_state TEXT NOT NULL CONSTRAINT ck_activation_result CHECK (result_state IN ('ACTIVE','INACTIVE','FAIL_CLOSED')),
    safe_failure_code TEXT,
    recorded_at TEXT NOT NULL,
    audit_id INTEGER NOT NULL,
    CONSTRAINT uq_activation_idempotency UNIQUE (installation_id,idempotency_key),
    CONSTRAINT ck_activation_combination CHECK (
        (secret_validation='VALID' AND provenance_validation='VALID' AND requested_state='ACTIVE' AND result_state='ACTIVE') OR
        (requested_state='ACTIVE' AND result_state='FAIL_CLOSED' AND (secret_validation IN ('INVALID','UNAVAILABLE') OR provenance_validation IN ('INVALID','UNAVAILABLE'))) OR
        (requested_state='INACTIVE' AND result_state='INACTIVE')
    ),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (clone_decision_id) REFERENCES clone_decision(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (compatibility_decision_id) REFERENCES compatibility_decision(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
