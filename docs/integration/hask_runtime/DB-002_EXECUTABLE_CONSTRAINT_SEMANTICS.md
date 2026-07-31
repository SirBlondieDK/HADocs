# DB-002 Executable Constraint Semantics Clarification

Status: **COMPLETE**  
Authority: `governance/active/DB-002.md`  
Type: normative architecture supplement; no implementation

## 1. Purpose, precedence and notation

This document resolves only the three executable ambiguities recorded by
`IM-001_BATCH2_BLOCKER_REPORT.md`. It supplements, and does not modify,
`DB-001_HASK_DATABASE_FOUNDATION.md` at SHA-256
`676e5cca648bf894eb69c1329371819e272fade44eba5ff9130fc3d1d0491e79`.

DB-001 remains authoritative for all tables, columns, keys, foreign keys,
indexes, ownership, retention, phases and unit-of-work allocation. DB-002 is
authoritative only for stored literals, combinations, conditional presence,
trigger semantics and LifecycleHistory disposition. If the two documents are
read together, no implementation choice remains in those areas.

Normative terms SHALL, MUST, MUST NOT, MAY and SHOULD have their ordinary RFC
2119 meanings. Stored text is case-sensitive ASCII unless explicitly described
as canonical JSON. Input aliases MAY be normalized only before persistence;
aliases MUST NOT be persisted. An unknown input value is rejected before write
and, where activation or identity is involved, produces the already accepted
fail-closed boundary. In every matrix below, rows not explicitly ALLOWED or
REQUIRED are **FORBIDDEN**. `N/A` means the column is required to be NULL or the
operation does not apply.

## 2. Stable decisions

| ID | Decision | Reason | Consequences | Compatibility effect | Revisit trigger |
|---|---|---|---|---|---|
| DB002-D-001 | Persist canonical uppercase ASCII literals exactly as registered below; persist no alias. | One byte representation is required for deterministic checks and replay. | Input normalization precedes SQLite; unknown values fail closed. | Existing public Contract 1.0.0 values are mapped at the boundary and remain unchanged. | A governed public/internal enum revision. |
| DB002-D-002 | Every CHK field uses one named closed domain or an exact structural predicate; cross-column rules use closed allowlists with unlisted combinations forbidden. | Eliminates unspecified CHECK semantics. | Batch 2 can mechanically compare expected and actual checks. | Database-internal values are not new public contract values. | A new accepted state or taxonomy class. |
| DB002-D-003 | Conditional presence and terminality are status-driven only; elapsed time and repeated scans never change classification. | Preserves AI-002 absence/removal and DB-001 retention semantics. | NULL/non-NULL rules are deterministic. | No Contract 1.0.0 change. | A governed lifecycle revision. |
| DB002-D-004 | Trigger-controlled rows use the exact transition matrices and mutable-column allowlists below; immutable families reject UPDATE and DELETE. | Prevents triggers from inventing or weakening workflows. | SQLite enforces shape; Batch 3 still owns semantic authorization and audit/UoW coordination. | Internal only. | SQLite capability failure or governed transaction redesign. |
| DB002-D-005 | LifecycleHistory is the physical read-only SQLite view `lifecycle_history` over entity and relationship event histories. | DB-001 calls it a query/view and Batch 2 requires physical conformance. | No 26th table or persistence owner is created. Callers supply ordering. | View is internal and does not alter Contract 1.0.0. | A governed history-query contract revision. |
| DB002-D-006 | The conformance manifest in section 12 is the complete Batch 2 handoff; deviations must equal zero. | Implementation must make no architectural choice. | IM-001 requires a later explicit reactivation transition. | Contract 2.0.0 remains inactive. | Independent review finds an objective omission or contradiction. |

## 3. Canonical domain registry

### 3.1 Universal storage policy

- Text literals: exact uppercase ASCII; binary collation; no surrounding space.
- Aliases accepted at persistence boundary: **none**. A collector/config adapter
  may map a documented external spelling before the database call.
- Defaults: only DB-001's `singleton_key=1` and
  `observation_contribution=0`; no other CHK field has a default.
- Nullable CHK fields: only `entity_lifecycle_event.prior_state` and
  `scan_capability_outcome.retryable`; their NULL rules are in section 6.
- Versions/generations: INTEGER `>= 0`, except declaration, secret and format
  generations which are INTEGER `>= 1`.
- Boolean: INTEGER exactly `0` or `1`.
- JSON object: UTF-8 TEXT accepted only when SQLite `json_valid(value)=1` and
  `json_type(value)='object'`. Canonical key ordering/minification is the
  application-validation owner from DB-001; SQLite owns structural validity.

### 3.2 Closed text domains

| Domain | Complete canonical literals | Terminal literals | Meaning/authority |
|---|---|---|---|
| `installation_state` | `ACTIVE`, `RETIRED` | `RETIRED` | Logical installation current/retired; DB-001 retention. |
| `integrity_state` | `VALID`, `INVALID`, `UNKNOWN` | `INVALID` | Validated, proven invalid, not established; fail closed unless VALID. |
| `availability_state` | `AVAILABLE`, `UNAVAILABLE` | none | Current access fact; unavailability is not invalidity. |
| `identity_status` | `ACTIVE`, `RETIRED`, `IDENTITY_INVALID` | `RETIRED` | Accepted current, governed retirement, present invalid identity; AI-002. |
| `scan_status` | `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED`, `CANCELLED` | all except `RUNNING` | One collection attempt outcome; DB-001 LC-018. |
| `scan_completeness` | `PENDING`, `COMPLETE`, `PARTIAL`, `UNAVAILABLE` | all except `PENDING` | Scope completeness; absence reasoning only under COMPLETE. |
| `taxonomy_class` | `A`, `B`, `C`, `D`, `E`, `F`, `G` | N/A | Only durable DB-001C classes; H–L never enter this table. |
| `authority_class` | `AUTHORITATIVE_FACT`, `STRUCTURED_CONTEXT_DEPENDENT` | N/A | Persistable authority classes; unsafe inference is rejected. |
| `privacy_class` | `PUBLIC`, `LOCAL_ONLY`, `SENSITIVE` | N/A | `SECRET` is never persistable. |
| `retention_policy` | `MUST_RETAIN`, `RETAIN_UNTIL_SUPERSEDED`, `RETAIN_FOR_AUDIT`, `CONFIGURABLE_HISTORY` | N/A | Sole durable policies for A–G. |
| `compatibility_result` | `COMPATIBLE`, `CONDITIONALLY_COMPATIBLE`, `INCOMPATIBLE`, `UNKNOWN` | all | AI-002 version compatibility result. |
| `capability_outcome` | `CAPABILITY_ENABLED`, `CAPABILITY_LIMITED`, `CAPABILITY_FAIL_CLOSED` | all | Runtime boundary only; not a score or confirmation. |
| `audit_event_kind` | `INSTALLATION_CREATED`, `INSTALLATION_RETIRED`, `CONTEXT_ACTIVATED`, `CONTEXT_SUPERSEDED`, `IDENTITY_REGISTERED`, `IDENTITY_RETIRED`, `ENTITY_TRANSITIONED`, `RELATIONSHIP_TRANSITIONED`, `SCAN_TERMINATED`, `CLONE_DECIDED`, `COMPATIBILITY_DECIDED`, `ACTIVATION_RECORDED`, `MIGRATION_STARTED`, `MIGRATION_SUCCEEDED`, `MIGRATION_FAILED`, `RETENTION_EXECUTED`, `BUNDLE_ACTIVATED`, `BUNDLE_ROLLED_BACK` | N/A | Closed audit event vocabulary for DB-001 UoWs. |
| `audit_outcome` | `SUCCEEDED`, `FAILED`, `REJECTED`, `NO_OP` | all | Safe operation result. |
| `validation_state` | `PENDING`, `VALID`, `INVALID`, `UNAVAILABLE` | `VALID`, `INVALID`, `UNAVAILABLE` | Validation gate; only VALID permits activation. |
| `migration_state_status` | `IDLE`, `RUNNING`, `BLOCKED` | N/A | Coordinator status; BLOCKED requires recovery. |
| `context_status` | `ACTIVE`, `SUPERSEDED` | `SUPERSEDED` | Retained installation lineage. |
| `clone_classification` | `SAME_LOGICAL_INSTALLATION`, `DISTINCT_LOGICAL_INSTALLATION`, `UNKNOWN` | all | AI-002 clone classification. |
| `ambiguity_state` | `RESOLVED`, `UNRESOLVED` | all | Classification evidence closure. |
| `clone_activation_outcome` | `PRESERVE_CONTEXT`, `NEW_CONTEXT_REQUIRED`, `FAIL_CLOSED` | all | AI-002 deterministic outcome. |
| `protected_validation` | `VALID`, `INVALID`, `UNAVAILABLE` | all | Secret/provenance validation without material exposure. |
| `activation_requested_state` | `ACTIVE`, `INACTIVE` | N/A | Requested installation-context activation state. |
| `activation_result_state` | `ACTIVE`, `INACTIVE`, `FAIL_CLOSED` | all | Recorded outcome; fail closed emits no new identity state. |
| `declaration_authority_status` | `AUTHORITATIVE`, `REVOKED` | `REVOKED` | Protected declaration authority. |
| `reference_kind` | `entity`, `device`, `area`, `label` | N/A | Exact lowercase CA-001 reference-kind bytes; sole lowercase exception. |
| `entity_lifecycle_state` | `ACTIVE`, `NOT_OBSERVED`, `UNAVAILABLE`, `REMOVED`, `IDENTITY_INVALID` | none | Closed five-state AI-002 current model; HISTORICAL excluded. |
| `relationship_current_status` | `CURRENT`, `CURRENT_ABSENT`, `CAPABILITY_FAIL_CLOSED` | none | Current tuple, explicit absence, or closed capability boundary. |
| `relationship_event_kind` | `CREATED`, `REPLACED`, `REMOVED`, `RECREATED` | all | Immutable relationship transition event. |
| `relationship_continuity` | `PRESERVED`, `DISCONTINUOUS`, `UNKNOWN` | all | Same tuple identity, replacement context, or unresolved/fail-closed. |
| `capability_status` | `SUCCEEDED`, `FAILED`, `UNAVAILABLE`, `UNSUPPORTED` | all | Terminal capability outcome within a run. |
| `completeness_contribution` | `COMPLETE`, `PARTIAL`, `NONE` | all | Contribution to enclosing run completeness. |
| `migration_attempt_status` | `PLANNED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED` | `SUCCEEDED`, `FAILED`, `INTERRUPTED` | Ordered attempt lifecycle. |
| `recovery_validation` | `NOT_REQUIRED`, `VALID`, `INVALID`, `UNAVAILABLE` | all | Pre-migration recovery-set gate. |
| `subject_kind` | `LOGICAL_INSTALLATION`, `INSTALLATION_CONTEXT`, `IDENTITY_REGISTRATION`, `ENTITY`, `RELATIONSHIP`, `SCAN_RUN`, `OBSERVATION`, `CLONE_DECISION`, `COMPATIBILITY_DECISION`, `ACTIVATION_OUTCOME`, `MIGRATION_ATTEMPT`, `AUDIT_RECORD` | N/A | Closed tagged-subject roots; transaction service validates target existence. |

### 3.3 CHK-controlled field registry (63 fields)

Every row inherits case, alias, NULL and default rules from 3.1. `Contract`
means exact accepted architecture terminology may be safely exported;
`internal` means the literal is never a new Contract 1.0.0 value.

| Table.column | Domain/predicate | Contract | Authority |
|---|---|---|---|
| logical_installation.state | installation_state | internal | DB-001 LC-030/retention |
| collision_registry.integrity_status | integrity_state | internal | CA-001 collision integrity |
| collision_registry.availability_status | availability_state | internal | DB-001 recovery |
| collision_registry.format_version | INTEGER >= 1 | internal | CA-001 format |
| entity.identity_status | identity_status | internal | AI-002 removal/identity |
| relationship.identity_status | identity_status | internal | AI-002 relationship identity |
| scan_run.status | scan_status | internal | DB-001 LC-018 |
| scan_run.completeness | scan_completeness | internal | DB-001 LC-019 |
| observation.taxonomy_class | taxonomy_class | internal | DB-001C |
| observation.authority_class | authority_class | internal | Collector architecture |
| observation.normalized_payload_json | JSON object | internal | DB-001 normalization |
| observation.privacy_class | privacy_class | internal | DB-001C privacy |
| observation.retention_policy | retention_policy | internal | DB-001C |
| compatibility_decision.version_vector_json | JSON object | internal | AI-002 version vector |
| compatibility_decision.result | compatibility_result | Contract | AI-002 |
| compatibility_decision.capability_outcome | capability_outcome | internal | AI-002 fail-closed boundary |
| audit_record.event_kind | audit_event_kind | internal | DB-001 UoWs |
| audit_record.schema_version | INTEGER >= 0 | internal | DB001-D-008 |
| audit_record.outcome | audit_outcome | internal | DB-001 audit |
| version_state.singleton_key | INTEGER = 1, default 1 | internal | DB-001 singleton |
| version_state.schema_version | INTEGER >= 0 | internal | DB001-D-008 |
| version_state.hask_compatibility_status | compatibility_result | internal | bundle compatibility |
| version_state.validation_status | validation_state | internal | startup gate |
| migration_state.singleton_key | INTEGER = 1, default 1 | internal | DB-001 singleton |
| migration_state.current_schema_version | INTEGER >= 0 | internal | DB001-D-008 |
| migration_state.status | migration_state_status | internal | DB-001 migration UoW |
| migration_state.validation_status | validation_state | internal | migration gate |
| installation_context.secret_generation | INTEGER >= 1 | internal | CA-001 lifecycle |
| installation_context.format_version | INTEGER >= 1 | internal | CA-001 format |
| installation_context.status | context_status | internal | AI-002 continuity |
| clone_decision.classification | clone_classification | Contract terminology | AI-002 clone spec |
| clone_decision.ambiguity_state | ambiguity_state | internal | AI-002 ambiguity gate |
| clone_decision.activation_outcome | clone_activation_outcome | internal | AI-002 clone spec |
| activation_outcome.secret_validation | protected_validation | internal | CA-001 |
| activation_outcome.provenance_validation | protected_validation | internal | AI-002 provenance |
| activation_outcome.requested_state | activation_requested_state | internal | DB-001 activation UoW |
| activation_outcome.result_state | activation_result_state | internal | DB-001 activation UoW |
| authoritative_declaration.declaration_version | INTEGER >= 1 | internal | AI-002 declaration |
| authoritative_declaration.authority_status | declaration_authority_status | internal | AI-002 authority precedence |
| authoritative_declaration.integrity_status | integrity_state | internal | protected declaration |
| protected_provenance_reference.integrity_status | integrity_state | internal | AI-002 provenance |
| protected_provenance_reference.availability_status | availability_state | internal | AI-002 provenance |
| identity_registration.reference_kind | reference_kind | internal CA-001 bytes | CA-001 section 4 |
| identity_registration.format_version | INTEGER >= 1 | internal | CA-001 format |
| identity_registration.secret_generation | INTEGER >= 1 | internal | CA-001 lifecycle |
| identity_registration.status | identity_status | internal | collision retention |
| entity_current_state.lifecycle_state | entity_lifecycle_state | Contract terminology | AI-002 removal semantics |
| entity_lifecycle_event.prior_state | entity_lifecycle_state or NULL | Contract terminology | AI-002 transition matrix |
| entity_lifecycle_event.result_state | entity_lifecycle_state | Contract terminology | AI-002 transition matrix |
| relationship_current_state.status | relationship_current_status | internal | AI-002 relationship spec |
| relationship_lifecycle_event.event_kind | relationship_event_kind | internal | AI-002 relationship lifecycle |
| relationship_lifecycle_event.continuity | relationship_continuity | internal | AI-002 continuity |
| scan_capability_outcome.status | capability_status | internal | scan completeness |
| scan_capability_outcome.retryable | BOOLEAN or NULL | internal | safe failure metadata |
| scan_capability_outcome.observation_contribution | BOOLEAN, default 0 | internal | DB-001 collection facts |
| scan_capability_outcome.completeness_contribution | completeness_contribution | internal | DB-001 completeness |
| migration_attempt.from_version | INTEGER >= 0 | internal | DB001-D-008 |
| migration_attempt.to_version | INTEGER = from_version + 1 | internal | forward-only migration |
| migration_attempt.status | migration_attempt_status | internal | DB-001 migration policy |
| migration_attempt.recovery_set_validation | recovery_validation | internal | DB-001 recovery gate |
| observation_subject_link.subject_kind | subject_kind | internal | LC-024 |
| audit_evidence_link.ordinal | INTEGER >= 0 | internal | deterministic evidence order |
| audit_subject_link.subject_kind | subject_kind | internal | LC-024 |

## 4. Complete combination matrices

Only listed rows are allowed; this convention makes each matrix exhaustive.

### 4.1 Installation, collision, context and identity

| Object | Combination | Disposition |
|---|---|---|
| logical_installation | ACTIVE + retired_at NULL | REQUIRED |
| logical_installation | RETIRED + retired_at NOT NULL | REQUIRED |
| collision_registry | VALID + AVAILABLE | REQUIRED for operational activation |
| collision_registry | VALID + UNAVAILABLE | ALLOWED, writes fail closed |
| collision_registry | INVALID + either availability | ALLOWED, writes fail closed |
| collision_registry | UNKNOWN + either availability | ALLOWED, writes fail closed |
| installation_context | ACTIVE + valid_until NULL | REQUIRED |
| installation_context | SUPERSEDED + valid_until NOT NULL | REQUIRED |
| identity_registration | ACTIVE + retired_at NULL | REQUIRED |
| identity_registration | RETIRED + retired_at NOT NULL | REQUIRED |
| identity_registration | IDENTITY_INVALID + retired_at NULL | REQUIRED |
| entity/relationship | ACTIVE, RETIRED or IDENTITY_INVALID | ALLOWED; current/history semantics remain separate |

### 4.2 Entity and relationship lifecycle

| Family | Combination | Disposition |
|---|---|---|
| entity current | each of five entity_lifecycle_state values | ALLOWED |
| entity creation event | prior_state NULL + any result_state | ALLOWED |
| entity later event | prior_state NOT NULL + any result_state permitted by AI-002 matrix | ALLOWED |
| relationship current | CURRENT + predicate/source_ref/target_ref all NOT NULL | REQUIRED |
| relationship current | CURRENT_ABSENT + tuple columns all NULL | REQUIRED |
| relationship current | CAPABILITY_FAIL_CLOSED + tuple columns all NULL | REQUIRED |
| relationship CREATED/RECREATED event | prior tuple all NULL + result tuple all NOT NULL | REQUIRED |
| relationship REPLACED event | prior tuple all NOT NULL + result tuple all NOT NULL | REQUIRED |
| relationship REMOVED event | prior tuple all NOT NULL + result tuple all NULL | REQUIRED |
| continuity PRESERVED | CREATED, RECREATED or REPLACED with same accepted identity context | ALLOWED |
| continuity DISCONTINUOUS | REPLACED with different accepted context | ALLOWED |
| continuity UNKNOWN | no current tuple publication; fail closed | REQUIRED |

The entity lifecycle result is the following complete current-state matrix;
`HISTORICAL` is a retention designation and never a current value:

| prior \ evidenced result | ACTIVE | NOT_OBSERVED | REMOVED | UNAVAILABLE | IDENTITY_INVALID |
|---|---|---|---|---|---|
| no prior identity | ALLOWED | ALLOWED | ALLOWED only with identifiable authoritative removal target | ALLOWED | ALLOWED |
| ACTIVE | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| NOT_OBSERVED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| REMOVED | ALLOWED only as positively evidenced recreation | FORBIDDEN; continued absence retains REMOVED | ALLOWED | ALLOWED | ALLOWED |
| UNAVAILABLE | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| IDENTITY_INVALID | ALLOWED only after validation | ALLOWED | ALLOWED only with identifiable authoritative removal target | ALLOWED | ALLOWED |

Each ALLOWED cell still requires the positive evidence stated by AI-002; the
matrix never makes absence, elapsed time or unavailability prove removal.

### 4.3 Scan and capability outcomes

| scan status | completeness | terminal_at | safe_error_code | Disposition |
|---|---|---|---|---|
| RUNNING | PENDING | NULL | NULL | REQUIRED |
| SUCCEEDED | COMPLETE | NOT NULL | NULL | ALLOWED |
| SUCCEEDED | PARTIAL | NOT NULL | NULL | ALLOWED |
| FAILED | PARTIAL or UNAVAILABLE | NOT NULL | NOT NULL | ALLOWED |
| INTERRUPTED | PARTIAL or UNAVAILABLE | NOT NULL | NOT NULL | ALLOWED |
| CANCELLED | PARTIAL or UNAVAILABLE | NOT NULL | NULL or NOT NULL | ALLOWED |

| capability status | retryable | safe_error_code | observation contribution | completeness contribution | Disposition |
|---|---|---|---|---|---|
| SUCCEEDED | NULL | NULL | 0 or 1 | COMPLETE or PARTIAL | ALLOWED |
| FAILED | 0 or 1 | NOT NULL | 0 | PARTIAL or NONE | ALLOWED |
| UNAVAILABLE | 0 or 1 | NULL or NOT NULL | 0 | PARTIAL or NONE | ALLOWED |
| UNSUPPORTED | NULL | NULL | 0 | NONE | REQUIRED |

### 4.4 Observation taxonomy

| taxonomy | sole retention | authority | privacy | Disposition |
|---|---|---|---|---|
| A | MUST_RETAIN | AUTHORITATIVE_FACT | LOCAL_ONLY or SENSITIVE | ALLOWED |
| B | RETAIN_UNTIL_SUPERSEDED | either authority | PUBLIC or LOCAL_ONLY | ALLOWED |
| C | RETAIN_UNTIL_SUPERSEDED | either authority | PUBLIC or LOCAL_ONLY | ALLOWED |
| D | RETAIN_FOR_AUDIT | either authority | LOCAL_ONLY or SENSITIVE | ALLOWED |
| E | RETAIN_FOR_AUDIT | either authority | PUBLIC or LOCAL_ONLY | ALLOWED |
| F | MUST_RETAIN | either authority | LOCAL_ONLY or SENSITIVE | ALLOWED |
| G | CONFIGURABLE_HISTORY | either authority | LOCAL_ONLY or SENSITIVE | ALLOWED |

H–L and `SECRET` privacy are FORBIDDEN in `observation` because DB-001C assigns
them discard/regenerate/memory behavior rather than durable rows.

### 4.5 Compatibility and validation

| compatibility result | capability outcome | Disposition |
|---|---|---|
| COMPATIBLE | CAPABILITY_ENABLED | REQUIRED |
| CONDITIONALLY_COMPATIBLE | CAPABILITY_LIMITED | REQUIRED |
| INCOMPATIBLE | CAPABILITY_FAIL_CLOSED | REQUIRED |
| UNKNOWN | CAPABILITY_FAIL_CLOSED | REQUIRED |

`version_state.validation_status=VALID` is required before operational use.
PENDING, INVALID or UNAVAILABLE block activation. HASK compatibility uses the
same four results; only COMPATIBLE or CONDITIONALLY_COMPATIBLE may accompany
VALID, and a conditionally compatible provider remains capability-limited.

### 4.6 Clone and activation

| classification | ambiguity | activation outcome | Disposition |
|---|---|---|---|
| SAME_LOGICAL_INSTALLATION | RESOLVED | PRESERVE_CONTEXT | REQUIRED normally |
| SAME_LOGICAL_INSTALLATION | RESOLVED | FAIL_CLOSED | ALLOWED only for known continuity with unavailable required secret/provenance |
| DISTINCT_LOGICAL_INSTALLATION | RESOLVED | NEW_CONTEXT_REQUIRED | REQUIRED |
| UNKNOWN | UNRESOLVED | FAIL_CLOSED | REQUIRED |

| secret validation | provenance validation | requested | result | Disposition |
|---|---|---|---|---|
| VALID | VALID | ACTIVE | ACTIVE | REQUIRED for activation success |
| any pair containing INVALID or UNAVAILABLE | ACTIVE | FAIL_CLOSED | REQUIRED |
| any allowed pair | INACTIVE | INACTIVE | ALLOWED |

### 4.7 Declaration/provenance and bundle state

| Object | Combination | Disposition |
|---|---|---|
| declaration | AUTHORITATIVE + VALID | eligible evidence |
| declaration | AUTHORITATIVE + UNKNOWN | retained, not eligible |
| declaration | REVOKED + any integrity | retained, not eligible |
| provenance | VALID + AVAILABLE | eligible evidence |
| provenance | any other pair | retained, fail closed |
| bundle state | VALID + COMPATIBLE | activation allowed |
| bundle state | VALID + CONDITIONALLY_COMPATIBLE | limited activation allowed |
| bundle state | PENDING/INVALID/UNAVAILABLE or INCOMPATIBLE/UNKNOWN | activation forbidden |
| version rollback refs | previous and rollback refs follow section 6 | internal recovery only |

### 4.8 Migration

| coordinator status | active_attempt_id | validation | Disposition |
|---|---|---|---|
| IDLE | NULL | VALID | normal stable state |
| RUNNING | NOT NULL | PENDING | migration executing |
| BLOCKED | NOT NULL | INVALID or UNAVAILABLE | recovery required |

| attempt status | finished_at | safe_error_code | audit_id | recovery validation | Disposition |
|---|---|---|---|---|---|
| PLANNED | NULL | NULL | NULL | VALID or NOT_REQUIRED | ALLOWED |
| RUNNING | NULL | NULL | NULL | VALID or NOT_REQUIRED | ALLOWED |
| SUCCEEDED | NOT NULL | NULL | NOT NULL | VALID or NOT_REQUIRED | REQUIRED |
| FAILED | NOT NULL | NOT NULL | NOT NULL | any value | REQUIRED |
| INTERRUPTED | NOT NULL | NOT NULL | NOT NULL | any value | REQUIRED |

### 4.9 Audit and tagged subjects

`audit_record.safe_failure_code` MUST be NULL for SUCCEEDED and NO_OP and MUST
be NOT NULL for FAILED and REJECTED. Every `audit_event_kind` is compatible with
all four outcomes except `INSTALLATION_CREATED`, `CONTEXT_ACTIVATED`,
`IDENTITY_REGISTERED`, `MIGRATION_SUCCEEDED`, `BUNDLE_ACTIVATED` and
`BUNDLE_ROLLED_BACK`, which allow SUCCEEDED or NO_OP only. Failed attempts use
their corresponding attempt event (`ACTIVATION_RECORDED`, `MIGRATION_FAILED`)
rather than a success-kind row.

Tagged subject IDs MUST be positive. `subject_kind` determines the exact table
named by its literal. `OBSERVATION` is permitted in audit subjects but an
observation's own subject link uses only installation/context/registration/
entity/relationship/scan/decision/attempt roots. Evidence ordinals start at 0,
are unique per audit through the accepted alternate key, and are contiguous;
contiguity remains transaction-service enforced.

## 5. Conditional-presence rule catalogue

| ID | Table | WHEN | THEN | DB owner | Test obligation |
|---|---|---|---|---|---|
| CP-001 | logical_installation | state ACTIVE/RETIRED | retired_at NULL/NOT NULL respectively | CHECK | both states plus mismatch |
| CP-002 | installation_context | status ACTIVE/SUPERSEDED | valid_until NULL/NOT NULL | CHECK + trigger | creation/supersession/repeat |
| CP-003 | identity_registration | status ACTIVE/RETIRED/IDENTITY_INVALID | retired_at NULL/NOT NULL/NULL | CHECK + trigger | all combinations |
| CP-004 | scan_run | RUNNING | terminal_at and safe_error_code NULL; completeness PENDING | CHECK + trigger | running mutation |
| CP-005 | scan_run | terminal status | terminal_at NOT NULL; completeness not PENDING | CHECK + trigger | every terminal status |
| CP-006 | scan_run | FAILED or INTERRUPTED | safe_error_code NOT NULL | CHECK | missing failure code |
| CP-007 | scan_capability_outcome | SUCCEEDED/UNSUPPORTED | retryable NULL and safe_error_code NULL | CHECK | both statuses |
| CP-008 | scan_capability_outcome | FAILED | retryable NOT NULL and safe_error_code NOT NULL | CHECK | nullable failures |
| CP-009 | entity_lifecycle_event | creation (no predecessor event) | prior_state NULL | CHECK/application evidence | initial event |
| CP-010 | entity_lifecycle_event | non-creation | prior_state NOT NULL | CHECK/application evidence | later event |
| CP-011 | relationship_current_state | CURRENT | all tuple columns NOT NULL | CHECK | tuple presence |
| CP-012 | relationship_current_state | CURRENT_ABSENT or CAPABILITY_FAIL_CLOSED | all tuple columns NULL | CHECK | tuple absence |
| CP-013 | relationship_lifecycle_event | CREATED/RECREATED | prior tuple NULL; result tuple NOT NULL | CHECK | both kinds |
| CP-014 | relationship_lifecycle_event | REPLACED | both tuples NOT NULL | CHECK | partial tuples |
| CP-015 | relationship_lifecycle_event | REMOVED | prior tuple NOT NULL; result tuple NULL | CHECK | result leakage |
| CP-016 | migration_state | IDLE/RUNNING/BLOCKED | active attempt NULL/NOT NULL/NOT NULL | CHECK | all coordinator states |
| CP-017 | migration_attempt | PLANNED/RUNNING | finished_at, error and audit NULL | CHECK + trigger | pre-terminal fields |
| CP-018 | migration_attempt | SUCCEEDED | finished_at/audit NOT NULL; error NULL | CHECK + trigger | success fields |
| CP-019 | migration_attempt | FAILED/INTERRUPTED | finished_at/error/audit NOT NULL | CHECK + trigger | failure fields |
| CP-020 | audit_record | SUCCEEDED/NO_OP versus FAILED/REJECTED | safe_failure_code NULL versus NOT NULL | CHECK | four outcomes |
| CP-021 | version_state | hask_activated_at NULL | previous and rollback refs NULL | CHECK | inactive bundle |
| CP-022 | version_state | hask_activated_at NOT NULL | previous ref MAY be NULL only for first activation; rollback ref MAY be NULL only when no validated rollback exists | transaction validation | first/later activation |
| CP-023 | compatibility_decision | context-less startup evaluation | context_id and scan_run_id MAY be NULL | application validation | startup case |
| CP-024 | compatibility_decision | scan evaluation | scan_run_id NOT NULL | application validation | scan case |
| CP-025 | authoritative_declaration | current version | valid_until NULL | CHECK + immutable supersession | current declaration |
| CP-026 | authoritative_declaration | superseded/revoked | valid_until NOT NULL | CHECK + immutable supersession | historical version |

## 6. Exact controlled-transition matrices

For every matrix, self-transition means an attempted UPDATE and is forbidden;
idempotency returns the existing row without issuing UPDATE.

### 6.1 installation_context

| FROM \ TO | ACTIVE | SUPERSEDED |
|---|---|---|
| ACTIVE | FORBIDDEN | ALLOWED |
| SUPERSEDED | FORBIDDEN | FORBIDDEN |

INSERT MUST be ACTIVE with `valid_until=NULL`. The sole UPDATE changes exactly
`status` from ACTIVE to SUPERSEDED and `valid_until` from NULL to one canonical
timestamp. No other column may change. A SUPERSEDED row is terminal and
immutable. DELETE is always forbidden.

### 6.2 identity_registration

| FROM \ TO | ACTIVE | RETIRED | IDENTITY_INVALID |
|---|---|---|---|
| ACTIVE | FORBIDDEN | ALLOWED | ALLOWED |
| RETIRED | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| IDENTITY_INVALID | FORBIDDEN | FORBIDDEN | FORBIDDEN |

INSERT MAY be ACTIVE or IDENTITY_INVALID, both with `retired_at=NULL`. The
ACTIVE→RETIRED transition changes exactly status and `retired_at` from NULL to a
canonical timestamp. ACTIVE→IDENTITY_INVALID changes only status; it records a
current validation failure and does not erase historical digest/reference.
RETIRED and IDENTITY_INVALID rows are terminal. DELETE is always forbidden.

### 6.3 scan_run

| FROM \ TO | RUNNING | SUCCEEDED | FAILED | INTERRUPTED | CANCELLED |
|---|---|---|---|---|---|
| RUNNING | FORBIDDEN | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| SUCCEEDED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| FAILED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| INTERRUPTED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| CANCELLED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |

INSERT MUST be RUNNING/PENDING. The one allowed terminalization changes exactly
`status`, `completeness`, `terminal_at` and `safe_error_code` under matrix 4.3.
All terminal rows are immutable. DELETE is forbidden while any retained
dependent exists; purge eligibility remains Batch 3 transaction-owned.

### 6.4 migration_attempt

| FROM \ TO | PLANNED | RUNNING | SUCCEEDED | FAILED | INTERRUPTED |
|---|---|---|---|---|---|
| PLANNED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | ALLOWED |
| RUNNING | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED | ALLOWED |
| SUCCEEDED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| FAILED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| INTERRUPTED | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |

PLANNED→RUNNING changes only status. A terminal transition changes exactly
status, `finished_at`, `safe_error_code` according to CP-018/019 and `audit_id`.
Failure never retries the row; retry is a new attempt with a new idempotency key
and the same released migration ID/checksum after recovery validation. DELETE is
always forbidden.

### 6.5 scan_capability_outcome

The row is inserted once with one terminal `capability_status`; there is no
non-terminal row state and no correction UPDATE. After insert, UPDATE and DELETE
are forbidden. A correction is a new ScanRun and new outcome row; it never
supersedes history in place.

## 7. Trigger semantic contract catalogue

| ID | Tables | Operations/predicate | Prohibited mutation / permitted exception | Error category | Recovery and tests |
|---|---|---|---|---|---|
| DB002-TR-001 | installation_context | BEFORE UPDATE/DELETE | only exact ACTIVE→SUPERSEDED allowlist; DELETE forbidden | CONSTRAINT_VIOLATION | retain row; test every edge/column |
| DB002-TR-002 | identity_registration | BEFORE UPDATE/DELETE | only two ACTIVE terminal transitions; DELETE forbidden | CONSTRAINT_VIOLATION | collision history retained; test all edges |
| DB002-TR-003 | scan_run | BEFORE UPDATE | only RUNNING→one terminal with CP rules | CONSTRAINT_VIOLATION | prior run retained; test all edges |
| DB002-TR-004 | migration_attempt | BEFORE UPDATE/DELETE | only matrix 6.4 fields; DELETE forbidden | MIGRATION_FAILURE | remain blocked/restore; test all edges |
| DB002-TR-005 | scan_capability_outcome | BEFORE UPDATE/DELETE | every mutation forbidden | CONSTRAINT_VIOLATION | new run for correction |
| DB002-TR-006 | authoritative_declaration, protected_provenance_reference | BEFORE UPDATE/DELETE | every mutation forbidden; supersede by INSERT | CONSTRAINT_VIOLATION | retain old version; test both operations/table |
| DB002-TR-007 | clone_decision, activation_outcome, observation, compatibility_decision, audit_record, entity_lifecycle_event, relationship_lifecycle_event, observation_subject_link, audit_evidence_link, audit_subject_link | BEFORE UPDATE/DELETE | every mutation forbidden | CONSTRAINT_VIOLATION | append corrective evidence only; test both operations/table |

INSERT triggers are not required: table CHECK/UNIQUE/FK constraints validate
insert shape, while Batch 3 transaction services own semantic authority. Trigger
failure messages SHALL expose only the stable ID above; repositories later map
to the listed canonical DB-001 error category without SQL or sensitive values.

## 8. LifecycleHistory physical-view contract

DB002-D-005 chooses a physical SQLite view.

- Stable name: `lifecycle_history`.
- Read-only: yes; SQLite view plus no INSTEAD OF triggers.
- Sources: `entity_lifecycle_event` joined to `entity`,
  `identity_registration`, `audit_record`; UNION ALL with
  `relationship_lifecycle_event` joined to `relationship`, `audit_record`.
- Duplicate semantics: UNION ALL; one output row per source event; no DISTINCT.
- Filtering: none inside the view. Callers scope by `installation_id`, kind,
  subject or time.
- Ordering: the view guarantees none. Callers MUST order by
  `(effective_at, history_kind, event_id)` for deterministic chronology.
- Rebuild: deterministic from retained source tables; the view stores no data.

Exact output column order:

| Ordinal | Column | Type/nullability | Entity row | Relationship row |
|---:|---|---|---|---|
| 1 | history_kind | TEXT NOT NULL | `ENTITY` | `RELATIONSHIP` |
| 2 | installation_id | INTEGER NOT NULL | entity installation | relationship installation |
| 3 | subject_id | INTEGER NOT NULL | entity id | relationship id |
| 4 | subject_ref | TEXT NOT NULL | registration opaque_reference | public_relationship_id |
| 5 | event_id | INTEGER NOT NULL | entity event id | relationship event id |
| 6 | event_kind | TEXT NOT NULL | `LIFECYCLE_TRANSITION` | relationship event_kind |
| 7 | prior_value_json | TEXT NULL | JSON object with `state`, or NULL | JSON tuple, or NULL |
| 8 | result_value_json | TEXT NULL | JSON object with `state` | JSON tuple, or NULL |
| 9 | effective_at | TEXT NOT NULL | event_at | event_at |
| 10 | recorded_at | TEXT NOT NULL | joined audit recorded_at | joined audit recorded_at |
| 11 | audit_id | INTEGER NOT NULL | source audit_id | source audit_id |
| 12 | observation_id | INTEGER NOT NULL | source observation_id | source observation_id |
| 13 | scan_run_id | INTEGER NOT NULL | source scan_run_id | source scan_run_id |
| 14 | reason_code | TEXT NULL | source reason_code | NULL |

Tuple JSON has exactly keys `predicate`, `source_ref`, `target_ref` in that
order. State JSON has exactly key `state`. JSON NULL source components yield SQL
NULL for the whole value. Actor/source is represented only through `audit_id`
and `observation_id`; no user, credential or secret is projected. Compatibility
is internal schema version 1; changing name, columns/order or row semantics
requires a governed schema migration and architecture review.

## 9. Contract 1.0.0 compatibility

Contract 1.0.0 is unchanged. Database literals fall into three classes:

1. Exact accepted architecture terminology: clone classification, entity
   lifecycle and compatibility results. Export MAY reuse the same spelling only
   where Contract 1.0.0 already exposes that field/value.
2. Internal operational literals: all coordinator, validation, trigger, audit,
   retention and relationship-current values. They are not automatically
   exported.
3. Boundary-mapped values: an existing Contract 1.0.0 lowercase or differently
   named value is converted by the future repository/projection owner to the
   registered internal literal before write and back only through the frozen
   contract allowlist.

Unknown external values are never coerced to UNKNOWN unless the governing
architecture explicitly defines UNKNOWN for that semantic domain. Otherwise
they are rejected. Future additive values remain unsupported until a governed
domain/schema migration exists. Contract 2.0.0 is inactive and has no mapping.

## 10. Conformance fixtures

The following documentation fixtures are normative test inputs, not executable
fixtures:

- each 3.3 field: every registered literal/predicate boundary passes; lowercase,
  whitespace, unknown and wrong-type cases fail;
- each section 4 matrix: every listed row passes; one mutation of every
  participating column fails;
- CP-001–CP-026: positive and negative pair;
- all 25 edges/cells in scan_run and migration_attempt matrices, all 9 cells in
  identity registration, all 4 context cells;
- DB002-TR-001–007: prohibited UPDATE and DELETE per covered table plus every
  explicit allowed transition;
- LifecycleHistory: schema/name/order, two source-family rows, UNION ALL
  duplicate preservation, no implicit ordering and write rejection.

## 11. Zero-deviation preservation proof

| Frozen DB-001 element | Expected | DB-002 result | Deviation |
|---|---:|---:|---:|
| Physical tables | 25 | unchanged | 0 |
| Physical columns | 243 | unchanged | 0 |
| INTEGER primary keys | 25 | unchanged | 0 |
| Alternate candidate keys | 28 | unchanged | 0 |
| Fixed foreign keys | 57 | unchanged | 0 |
| Logical constraints | 30 | clarified, not reallocated | 0 |
| Secondary indexes | 18 | unchanged | 0 |
| Fully immutable families | 11 | exact family trigger contract | 0 |
| Supersedable immutable families | 2 | exact family trigger contract | 0 |
| Migration phases | 8 | unchanged | 0 |
| Repository owners | 10 | unchanged | 0 |
| Public contract | 1.0.0 | unchanged | 0 |

The view is derived and does not change the 25-table/243-column counts.

## 12. Documentation-level conformance manifest

| Manifest item | Inventory | Expected Batch 2 artifact | Expected test category |
|---|---:|---|---|
| CHK-controlled fields | 63 (section 3.3) | table CHECK or allocated validator | field-domain introspection/boundaries |
| Closed text domains | 34 (section 3.2) | named deterministic CHECK fragments | every literal plus unknown/case |
| Structural predicates | 8 kinds: positive, non-negative, boolean, singleton, next-version, JSON object, nullable-domain, default | CHECK/default | numeric/JSON/default boundaries |
| Combination matrices | 9 families (section 4) | table/cross-column CHECK or allocated Batch 3 validator | every listed/unlisted combination |
| Conditional rules | 26 (CP-001–026) | CHECK, trigger or allocated validator exactly as named | positive/negative per rule |
| Transition matrices | 5 families (section 6) | named triggers for physical owners | every FROM×TO cell and column allowlist |
| Trigger semantic contracts | 7 (DB002-TR-001–007) | deterministic trigger set | UPDATE/DELETE/allowed-edge coverage |
| LifecycleHistory | physical view `lifecycle_history`, 14 columns | one CREATE VIEW artifact | shape/rows/order/write rejection |
| Contract mapping | three closed mapping classes | future projection boundary, no schema artifact | unknown/forward/internal exposure |

The 34 domain count treats each named domain once; canonical literals are
counted per domain, not deduplicated across semantically distinct domains. The
registry contains **138 domain-literal entries**. Reference-kind literals retain
the exact lowercase bytes required by CA-001; all other text entries are
uppercase ASCII.

## 13. Validation and completion

- Every DB-001 section 63 CHK field has exactly one domain/predicate: PASS (63).
- Every stored status has one spelling and aliases are never persisted: PASS.
- Combination and conditional rules use default-forbidden closure: PASS.
- Every trigger-controlled family has a complete transition/mutation contract:
  PASS.
- LifecycleHistory has one executable disposition: PASS, physical read-only
  view.
- Contract 1.0.0 unchanged and 2.0.0 inactive: PASS.
- Added/changed table, column, key, FK, index, owner, retention class, phase or
  UoW: 0.
- SQL, migration, code, test, fixture, repository or runtime implementation: 0.
- DB-001 modified: no.
- IM-001 Batch 2 resumed: no; it remains BLOCKED/PAUSED.
- Batches 3–5 authorized or started: no.
- Unresolved executable decisions: 0.

## 14. Handoff

DB-002 is **COMPLETE** and is a normative implementation supplement to DB-001.
This status does not resume or authorize IM-001. A separate governance
transition must independently accept this clarification and reactivate IM-001
Batch 2 before any SQL, migration, schema test or other implementation work.
