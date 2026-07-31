CREATE TABLE scan_run (
    id INTEGER PRIMARY KEY CHECK (id>0),
    installation_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    started_at TEXT NOT NULL,
    terminal_at TEXT,
    status TEXT NOT NULL CONSTRAINT ck_scan_run_status CHECK (status IN ('RUNNING','SUCCEEDED','FAILED','INTERRUPTED','CANCELLED')),
    completeness TEXT NOT NULL CONSTRAINT ck_scan_run_completeness CHECK (completeness IN ('PENDING','COMPLETE','PARTIAL','UNAVAILABLE')),
    safe_error_code TEXT,
    implementation_version TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    CONSTRAINT uq_scan_run_idempotency UNIQUE (installation_id,idempotency_key),
    CONSTRAINT ck_scan_run_combination CHECK (
        (status='RUNNING' AND completeness='PENDING' AND terminal_at IS NULL AND safe_error_code IS NULL) OR
        (status='SUCCEEDED' AND completeness IN ('COMPLETE','PARTIAL') AND terminal_at IS NOT NULL AND safe_error_code IS NULL) OR
        (status IN ('FAILED','INTERRUPTED') AND completeness IN ('PARTIAL','UNAVAILABLE') AND terminal_at IS NOT NULL AND safe_error_code IS NOT NULL) OR
        (status='CANCELLED' AND completeness IN ('PARTIAL','UNAVAILABLE') AND terminal_at IS NOT NULL)
    ),
    FOREIGN KEY (installation_id) REFERENCES logical_installation(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (context_id) REFERENCES installation_context(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE scan_capability_outcome (
    id INTEGER PRIMARY KEY CHECK (id>0),
    scan_run_id INTEGER NOT NULL,
    capability_id TEXT NOT NULL,
    status TEXT NOT NULL CONSTRAINT ck_capability_status CHECK (status IN ('SUCCEEDED','FAILED','UNAVAILABLE','UNSUPPORTED')),
    retryable INTEGER CONSTRAINT ck_capability_retryable CHECK (retryable IS NULL OR retryable IN (0,1)),
    safe_error_code TEXT,
    observation_contribution INTEGER NOT NULL DEFAULT 0 CONSTRAINT ck_capability_observation CHECK (observation_contribution IN (0,1)),
    completeness_contribution TEXT NOT NULL CONSTRAINT ck_capability_completeness CHECK (completeness_contribution IN ('COMPLETE','PARTIAL','NONE')),
    recorded_at TEXT NOT NULL,
    CONSTRAINT uq_capability_run UNIQUE (scan_run_id,capability_id),
    CONSTRAINT ck_capability_combination CHECK (
        (status='SUCCEEDED' AND retryable IS NULL AND safe_error_code IS NULL AND completeness_contribution IN ('COMPLETE','PARTIAL')) OR
        (status='FAILED' AND retryable IN (0,1) AND safe_error_code IS NOT NULL AND observation_contribution=0 AND completeness_contribution IN ('PARTIAL','NONE')) OR
        (status='UNAVAILABLE' AND retryable IN (0,1) AND observation_contribution=0 AND completeness_contribution IN ('PARTIAL','NONE')) OR
        (status='UNSUPPORTED' AND retryable IS NULL AND safe_error_code IS NULL AND observation_contribution=0 AND completeness_contribution='NONE')
    ),
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE observation (
    id INTEGER PRIMARY KEY CHECK (id>0),
    scan_run_id INTEGER NOT NULL,
    observation_key TEXT NOT NULL,
    taxonomy_class TEXT NOT NULL CONSTRAINT ck_observation_taxonomy CHECK (taxonomy_class IN ('A','B','C','D','E','F','G')),
    authority_class TEXT NOT NULL CONSTRAINT ck_observation_authority CHECK (authority_class IN ('AUTHORITATIVE_FACT','STRUCTURED_CONTEXT_DEPENDENT')),
    provenance_ref TEXT,
    observed_at TEXT NOT NULL,
    normalized_payload_json TEXT NOT NULL CONSTRAINT ck_observation_payload CHECK (json_valid(normalized_payload_json)=1 AND json_type(normalized_payload_json)='object'),
    privacy_class TEXT NOT NULL CONSTRAINT ck_observation_privacy CHECK (privacy_class IN ('PUBLIC','LOCAL_ONLY','SENSITIVE')),
    retention_policy TEXT NOT NULL CONSTRAINT ck_observation_retention CHECK (retention_policy IN ('MUST_RETAIN','RETAIN_UNTIL_SUPERSEDED','RETAIN_FOR_AUDIT','CONFIGURABLE_HISTORY')),
    immutable_digest BLOB NOT NULL CONSTRAINT ck_observation_digest CHECK (length(immutable_digest)=32),
    created_at TEXT NOT NULL,
    CONSTRAINT uq_observation_run_key UNIQUE (scan_run_id,observation_key),
    CONSTRAINT ck_observation_combination CHECK (
        (taxonomy_class='A' AND retention_policy='MUST_RETAIN' AND authority_class='AUTHORITATIVE_FACT' AND privacy_class IN ('LOCAL_ONLY','SENSITIVE')) OR
        (taxonomy_class IN ('B','C') AND retention_policy='RETAIN_UNTIL_SUPERSEDED' AND privacy_class IN ('PUBLIC','LOCAL_ONLY')) OR
        (taxonomy_class='D' AND retention_policy='RETAIN_FOR_AUDIT' AND privacy_class IN ('LOCAL_ONLY','SENSITIVE')) OR
        (taxonomy_class='E' AND retention_policy='RETAIN_FOR_AUDIT' AND privacy_class IN ('PUBLIC','LOCAL_ONLY')) OR
        (taxonomy_class='F' AND retention_policy='MUST_RETAIN' AND privacy_class IN ('LOCAL_ONLY','SENSITIVE')) OR
        (taxonomy_class='G' AND retention_policy='CONFIGURABLE_HISTORY' AND privacy_class IN ('LOCAL_ONLY','SENSITIVE'))
    ),
    FOREIGN KEY (scan_run_id) REFERENCES scan_run(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE observation_subject_link (
    id INTEGER PRIMARY KEY CHECK (id>0),
    observation_id INTEGER NOT NULL,
    subject_kind TEXT NOT NULL CONSTRAINT ck_observation_subject_kind CHECK (subject_kind IN ('LOGICAL_INSTALLATION','INSTALLATION_CONTEXT','IDENTITY_REGISTRATION','ENTITY','RELATIONSHIP','SCAN_RUN','CLONE_DECISION','COMPATIBILITY_DECISION','ACTIVATION_OUTCOME','MIGRATION_ATTEMPT')),
    subject_id INTEGER NOT NULL CONSTRAINT ck_observation_subject_id CHECK (subject_id>0),
    role TEXT NOT NULL,
    CONSTRAINT uq_observation_subject_role UNIQUE (observation_id,role),
    FOREIGN KEY (observation_id) REFERENCES observation(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
