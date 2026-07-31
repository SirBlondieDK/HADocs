CREATE TABLE audit_record (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    event_kind TEXT NOT NULL CONSTRAINT ck_audit_event_kind CHECK (event_kind IN ('INSTALLATION_CREATED','INSTALLATION_RETIRED','CONTEXT_ACTIVATED','CONTEXT_SUPERSEDED','IDENTITY_REGISTERED','IDENTITY_RETIRED','ENTITY_TRANSITIONED','RELATIONSHIP_TRANSITIONED','SCAN_TERMINATED','CLONE_DECIDED','COMPATIBILITY_DECIDED','ACTIVATION_RECORDED','MIGRATION_STARTED','MIGRATION_SUCCEEDED','MIGRATION_FAILED','RETENTION_EXECUTED','BUNDLE_ACTIVATED','BUNDLE_ROLLED_BACK')),
    recorded_at TEXT NOT NULL,
    authority TEXT NOT NULL,
    provenance_ref TEXT,
    architecture_version TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL CONSTRAINT ck_audit_schema_version CHECK (schema_version>=0),
    implementation_version TEXT NOT NULL,
    outcome TEXT NOT NULL CONSTRAINT ck_audit_outcome CHECK (outcome IN ('SUCCEEDED','FAILED','REJECTED','NO_OP')),
    safe_failure_code TEXT,
    CONSTRAINT uq_audit_idempotency UNIQUE (installation_id,idempotency_key),
    CONSTRAINT ck_audit_failure CHECK ((outcome IN ('SUCCEEDED','NO_OP') AND safe_failure_code IS NULL) OR (outcome IN ('FAILED','REJECTED') AND safe_failure_code IS NOT NULL)),
    CONSTRAINT ck_audit_success_kind CHECK (event_kind NOT IN ('INSTALLATION_CREATED','CONTEXT_ACTIVATED','IDENTITY_REGISTERED','MIGRATION_SUCCEEDED','BUNDLE_ACTIVATED','BUNDLE_ROLLED_BACK') OR outcome IN ('SUCCEEDED','NO_OP')),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE audit_evidence_link (
    id INTEGER PRIMARY KEY CHECK (id>0),
    audit_id INTEGER NOT NULL,
    observation_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    ordinal INTEGER NOT NULL CONSTRAINT ck_audit_evidence_ordinal CHECK (ordinal>=0),
    CONSTRAINT uq_audit_evidence_identity UNIQUE (audit_id,observation_id,role),
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (observation_id) REFERENCES observation(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE audit_subject_link (
    id INTEGER PRIMARY KEY CHECK (id>0),
    audit_id INTEGER NOT NULL,
    subject_kind TEXT NOT NULL CONSTRAINT ck_audit_subject_kind CHECK (subject_kind IN ('LOGICAL_INSTALLATION','INSTALLATION_CONTEXT','IDENTITY_REGISTRATION','ENTITY','RELATIONSHIP','SCAN_RUN','OBSERVATION','CLONE_DECISION','COMPATIBILITY_DECISION','ACTIVATION_OUTCOME','MIGRATION_ATTEMPT','AUDIT_RECORD')),
    subject_id INTEGER NOT NULL CONSTRAINT ck_audit_subject_id CHECK (subject_id>0),
    role TEXT NOT NULL,
    CONSTRAINT uq_audit_subject_identity UNIQUE (audit_id,subject_kind,subject_id,role),
    FOREIGN KEY (audit_id) REFERENCES audit_record(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX ix_context_installation_status ON installation_context(installation_id,status,valid_from);
CREATE INDEX ix_registration_registry_kind_status ON identity_registration(registry_id,reference_kind,status,registered_at);
CREATE INDEX ix_entity_installation_context_status ON entity(installation_id,context_id,identity_status,id);
CREATE INDEX ix_entity_state_value_time ON entity_current_state(lifecycle_state,effective_at,entity_id);
CREATE INDEX ix_entity_event_chronology ON entity_lifecycle_event(entity_id,event_at,id);
CREATE INDEX ix_relationship_traversal ON relationship(installation_id,predicate,source_ref,target_ref,id);
CREATE INDEX ix_relationship_state_time ON relationship_current_state(status,effective_at,relationship_id);
CREATE INDEX ix_relationship_event_chronology ON relationship_lifecycle_event(relationship_id,event_at,id);
CREATE INDEX ix_scan_installation_status_time ON scan_run(installation_id,status,started_at,id);
CREATE INDEX ix_capability_run_status ON scan_capability_outcome(scan_run_id,status,capability_id);
CREATE INDEX ix_observation_run_class_time ON observation(scan_run_id,taxonomy_class,observed_at,id);
CREATE INDEX ix_observation_subject ON observation_subject_link(subject_kind,subject_id,observation_id);
CREATE INDEX ix_compatibility_context_result_time ON compatibility_decision(installation_id,context_id,result,decided_at,id);
CREATE INDEX ix_audit_installation_kind_time ON audit_record(installation_id,event_kind,recorded_at,id);
CREATE INDEX ix_audit_evidence_observation ON audit_evidence_link(observation_id,audit_id);
CREATE INDEX ix_audit_subject ON audit_subject_link(subject_kind,subject_id,audit_id);
CREATE INDEX ix_migration_order_status ON migration_attempt(migration_state_id,to_version,status,started_at,id);
CREATE INDEX ix_external_versions ON version_state(hask_bundle_ref,hudd_ref,contract_version,validation_status);

CREATE TRIGGER db002_tr_001_installation_context_update BEFORE UPDATE ON installation_context
WHEN NOT (OLD.status='ACTIVE' AND NEW.status='SUPERSEDED' AND OLD.valid_until IS NULL AND NEW.valid_until IS NOT NULL AND NEW.id=OLD.id AND NEW.installation_id=OLD.installation_id AND NEW.predecessor_context_id IS OLD.predecessor_context_id AND NEW.installation_scope=OLD.installation_scope AND NEW.secret_handle=OLD.secret_handle AND NEW.secret_generation=OLD.secret_generation AND NEW.format_version=OLD.format_version AND NEW.valid_from=OLD.valid_from AND NEW.activation_audit_id=OLD.activation_audit_id)
BEGIN SELECT RAISE(ABORT,'DB002-TR-001'); END;
CREATE TRIGGER db002_tr_001_installation_context_delete BEFORE DELETE ON installation_context BEGIN SELECT RAISE(ABORT,'DB002-TR-001'); END;

CREATE TRIGGER db002_tr_002_identity_registration_update BEFORE UPDATE ON identity_registration
WHEN NOT (OLD.status='ACTIVE' AND ((NEW.status='RETIRED' AND OLD.retired_at IS NULL AND NEW.retired_at IS NOT NULL) OR (NEW.status='IDENTITY_INVALID' AND OLD.retired_at IS NULL AND NEW.retired_at IS NULL)) AND NEW.id=OLD.id AND NEW.registry_id=OLD.registry_id AND NEW.context_id=OLD.context_id AND NEW.reference_kind=OLD.reference_kind AND NEW.format_version=OLD.format_version AND NEW.canonical_tuple_handle=OLD.canonical_tuple_handle AND NEW.opaque_reference=OLD.opaque_reference AND NEW.secret_generation=OLD.secret_generation AND NEW.registered_at=OLD.registered_at AND NEW.registration_audit_id=OLD.registration_audit_id AND NEW.identity_digest=OLD.identity_digest)
BEGIN SELECT RAISE(ABORT,'DB002-TR-002'); END;
CREATE TRIGGER db002_tr_002_identity_registration_delete BEFORE DELETE ON identity_registration BEGIN SELECT RAISE(ABORT,'DB002-TR-002'); END;

CREATE TRIGGER db002_tr_003_scan_run_update BEFORE UPDATE ON scan_run
WHEN NOT (OLD.status='RUNNING' AND NEW.status IN ('SUCCEEDED','FAILED','INTERRUPTED','CANCELLED') AND NEW.id=OLD.id AND NEW.installation_id=OLD.installation_id AND NEW.context_id=OLD.context_id AND NEW.idempotency_key=OLD.idempotency_key AND NEW.started_at=OLD.started_at AND NEW.implementation_version=OLD.implementation_version AND NEW.contract_version=OLD.contract_version)
BEGIN SELECT RAISE(ABORT,'DB002-TR-003'); END;

CREATE TRIGGER db002_tr_004_migration_attempt_update BEFORE UPDATE ON migration_attempt
WHEN NOT (((OLD.status='PLANNED' AND NEW.status='RUNNING' AND NEW.finished_at IS OLD.finished_at AND NEW.safe_error_code IS OLD.safe_error_code AND NEW.audit_id IS OLD.audit_id) OR (OLD.status IN ('PLANNED','RUNNING') AND NEW.status IN ('SUCCEEDED','FAILED','INTERRUPTED'))) AND NEW.id=OLD.id AND NEW.migration_state_id=OLD.migration_state_id AND NEW.migration_id=OLD.migration_id AND NEW.idempotency_key=OLD.idempotency_key AND NEW.from_version=OLD.from_version AND NEW.to_version=OLD.to_version AND NEW.started_at=OLD.started_at AND NEW.recovery_set_validation=OLD.recovery_set_validation AND NEW.migration_checksum=OLD.migration_checksum)
BEGIN SELECT RAISE(ABORT,'DB002-TR-004'); END;
CREATE TRIGGER db002_tr_004_migration_attempt_delete BEFORE DELETE ON migration_attempt BEGIN SELECT RAISE(ABORT,'DB002-TR-004'); END;

CREATE TRIGGER db002_tr_005_capability_update BEFORE UPDATE ON scan_capability_outcome BEGIN SELECT RAISE(ABORT,'DB002-TR-005'); END;
CREATE TRIGGER db002_tr_005_capability_delete BEFORE DELETE ON scan_capability_outcome BEGIN SELECT RAISE(ABORT,'DB002-TR-005'); END;

CREATE TRIGGER db002_tr_006_declaration_update BEFORE UPDATE ON authoritative_declaration BEGIN SELECT RAISE(ABORT,'DB002-TR-006'); END;
CREATE TRIGGER db002_tr_006_declaration_delete BEFORE DELETE ON authoritative_declaration BEGIN SELECT RAISE(ABORT,'DB002-TR-006'); END;
CREATE TRIGGER db002_tr_006_provenance_update BEFORE UPDATE ON protected_provenance_reference BEGIN SELECT RAISE(ABORT,'DB002-TR-006'); END;
CREATE TRIGGER db002_tr_006_provenance_delete BEFORE DELETE ON protected_provenance_reference BEGIN SELECT RAISE(ABORT,'DB002-TR-006'); END;

CREATE TRIGGER db002_tr_007_clone_update BEFORE UPDATE ON clone_decision BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_clone_delete BEFORE DELETE ON clone_decision BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_activation_update BEFORE UPDATE ON activation_outcome BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_activation_delete BEFORE DELETE ON activation_outcome BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_observation_update BEFORE UPDATE ON observation BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_observation_delete BEFORE DELETE ON observation BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_compatibility_update BEFORE UPDATE ON compatibility_decision BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_compatibility_delete BEFORE DELETE ON compatibility_decision BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_update BEFORE UPDATE ON audit_record BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_delete BEFORE DELETE ON audit_record BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_entity_event_update BEFORE UPDATE ON entity_lifecycle_event BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_entity_event_delete BEFORE DELETE ON entity_lifecycle_event BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_relationship_event_update BEFORE UPDATE ON relationship_lifecycle_event BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_relationship_event_delete BEFORE DELETE ON relationship_lifecycle_event BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_observation_subject_update BEFORE UPDATE ON observation_subject_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_observation_subject_delete BEFORE DELETE ON observation_subject_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_evidence_update BEFORE UPDATE ON audit_evidence_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_evidence_delete BEFORE DELETE ON audit_evidence_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_subject_update BEFORE UPDATE ON audit_subject_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;
CREATE TRIGGER db002_tr_007_audit_subject_delete BEFORE DELETE ON audit_subject_link BEGIN SELECT RAISE(ABORT,'DB002-TR-007'); END;

CREATE VIEW lifecycle_history AS
SELECT 'ENTITY' AS history_kind, e.installation_id, ev.entity_id AS subject_id,
       ir.opaque_reference AS subject_ref, ev.id AS event_id,
       'LIFECYCLE_TRANSITION' AS event_kind,
       CASE WHEN ev.prior_state IS NULL THEN NULL ELSE json_object('state',ev.prior_state) END AS prior_value_json,
       json_object('state',ev.result_state) AS result_value_json,
       ev.event_at AS effective_at, ar.recorded_at, ev.audit_id, ev.observation_id,
       ev.scan_run_id, ev.reason_code
FROM entity_lifecycle_event ev
JOIN entity e ON e.id=ev.entity_id
JOIN identity_registration ir ON ir.id=e.identity_registration_id
JOIN audit_record ar ON ar.id=ev.audit_id
UNION ALL
SELECT 'RELATIONSHIP', r.installation_id, ev.relationship_id,
       r.public_relationship_id, ev.id, ev.event_kind,
       CASE WHEN ev.prior_predicate IS NULL AND ev.prior_source_ref IS NULL AND ev.prior_target_ref IS NULL THEN NULL ELSE json_object('predicate',ev.prior_predicate,'source_ref',ev.prior_source_ref,'target_ref',ev.prior_target_ref) END,
       CASE WHEN ev.result_predicate IS NULL AND ev.result_source_ref IS NULL AND ev.result_target_ref IS NULL THEN NULL ELSE json_object('predicate',ev.result_predicate,'source_ref',ev.result_source_ref,'target_ref',ev.result_target_ref) END,
       ev.event_at, ar.recorded_at, ev.audit_id, ev.observation_id,
       ev.scan_run_id, NULL
FROM relationship_lifecycle_event ev
JOIN relationship r ON r.id=ev.relationship_id
JOIN audit_record ar ON ar.id=ev.audit_id;
