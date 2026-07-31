# AI-002 Clone Architecture Decision Record

## Status and boundary

This intermediate record converts the completed Clone Analysis into explicit
design rationale for Batch 1B. It recommends an architecture shape and records
alternative dispositions. It is **not** the normative Clone Identity
Specification.

No clone classification rule, migration rule, lifecycle transition, rotation
trigger, output state, schema, implementation mechanism, source-reference rule,
removal semantic or version rule is defined here. Words such as “recommended”
and “preferred” identify design direction that Batch 1B must independently turn
into exact rules only where inherited authority supports them.

## Executive summary

No single Batch 1A strategy addresses intent, provenance, offline operation,
concurrent-copy risk and unknown evidence without violating another inherited
constraint. The recommended design direction is therefore a **combination**:

1. explicit authorized transition declaration as the direct expression of
   logical-installation intent;
2. protected lineage/provenance as durable evidence connecting creation,
   backup, restore, migration and identity generations;
3. a conservative ambiguity gate when the declaration or lineage cannot support
   a unique classification;
4. platform operation evidence and active uniqueness evidence only as bounded
   corroborating components, never as sole authority.

Always-preserve, always-rotate and environmental-fingerprint strategies are
rejected because each conflicts with established continuity, separation or
privacy constraints. This decision direction does not yet specify who may
declare, how declarations are authenticated, how lineage is encoded, what exact
unknown state results, or when scope/secret changes occur. Those remain gates
for Batch 1B.

## Decision objectives

The future specification needs a design basis capable of:

- distinguishing logical continuity from creation of a distinct installation;
- avoiding inference from copied bytes alone;
- preserving authorized restore/migration continuity;
- preventing silent identity sharing between distinct active installations;
- remaining deterministic with missing, conflicting or offline evidence;
- operating without a mandatory network or external key-management service;
- preserving accepted CA-001 cryptographic and privacy behavior;
- keeping secret, raw identity and sensitive lineage material out of public
  output and logs;
- making every future normative choice reviewable and traceable;
- stopping rather than delegating semantic choices to implementation.

These objectives restate inherited needs; they do not define their realization.

## Inherited architecture constraints

### DF-002

- DF-002 remains the implementation baseline and contract 1.0.0 remains active.
- Opaque identity is deterministic within one installation privacy context,
  stable for authorized cross-snapshot joins and non-correlatable across
  distinct installations.
- Secret local material and raw-to-opaque mappings remain outside public
  artifacts and logs.
- Unsafe identity handling fails closed for the affected capability.
- Release 1 remains four capabilities, four observation categories and four
  relationship predicates.

### AI-001

- Installation identity is a logical collector domain, not a hostname, address
  or account.
- Ordinary restart/update/configuration events preserve identity state.
- AI-001 proposed preserving identity for intended continuity and changing it
  for an intended new installation.
- Canonical-key, source-capability and observation-ID constructions remain
  frozen outside direct correction effects.
- R-003 found that AI-001 did not define who establishes clone intent or how
  that transition becomes authoritative.

### R-003

- R003-F-002 is a MAJOR normative defect affecting all categories.
- Copied state does not itself decide “same logical installation” versus “new
  installation.”
- A corrected architecture needs authoritative classification evidence, safe
  unknown treatment, rotation/continuity consequences and deterministic
  concurrent-clone behavior.
- Implementation cannot select one of several plausible interpretations.

### Accepted CA-001

- HMAC-SHA-256, secret length, framing, domain and full output are fixed and
  outside clone redesign.
- Equal kind/scope/raw ID under the same secret reproduces the same reference.
- Copying scope and secret copies the derivation context but does not classify
  the copy.
- Secret or scope change is identity-affecting.
- Ordinary restart, update, reload, transient read failure and ordinary restore
  are not automatic secret-rotation triggers.
- Exact-secret restoration can preserve intended continuity; automatic secret
  regeneration after loss is prohibited.
- Rotation occurs at an atomic snapshot boundary and cannot silently alias old
  and new identity.
- Hostname, address, filesystem path and machine ID do not participate in
  derivation.
- Private collision history is installation-wide within its identity context;
  copying it still does not prove global uniqueness.

### R-004 and focused verification

- The cryptographic construction and vectors are independently reproducible.
- Collision detection is installation-wide, durable, atomic and fail-closed.
- Secret language is exactly 32 cryptographically secure random octets.
- Scope separation is independently verified.
- CA-001 is accepted; clone classification remains an AI-002 decision surface,
  not a cryptographic defect to reopen.

## Ambiguity inventory from Batch 1A

| Ambiguity | Decision-synthesis treatment | Still open for Batch 1B? |
|---|---|---:|
| Copy versus move | Requires intent evidence plus lineage/source-disposition evidence; copied bytes alone are insufficient. | YES |
| Restore versus fork | Requires lineage capable of representing descendants and uncertainty about concurrent descendants. | YES |
| Same logical installation versus new installation | Requires an explicit authority/declaration path; environmental inference is insufficient. | YES |
| Valid local context versus globally unique active context | Local cryptographic validation cannot prove global uniqueness; corroborating concurrency evidence has bounded value. | YES |
| Planned migration versus unauthorized copy | Requires authoritative transition provenance; exact secret transfer proves continuity capability, not permission. | YES |
| Missing state versus intentionally fresh state | Requires prior-existence/lineage evidence or an ambiguity gate; absence alone is not intent. | YES |
| Hardware/environment drift versus identity transition | Hardware and environmental attributes cannot be identity roots; at most they can be non-authoritative context. | YES, exact exclusion/secondary role pending |
| Concurrent duplicate detection | Optional coordination may add evidence but cannot prove absence during partitions/air gaps. | YES |
| Secret rotation versus installation rotation | Their effects are related but not identical; exact coupling belongs in Batch 1B. | YES |
| Historical continuity after separation | Requires lineage without public aliasing or raw mappings; exact representation remains open. | YES |

Every ambiguity is addressed by the proposed design shape, but none receives a
normative outcome in this record.

## Decision-area inventory from Batch 1A

| Decision area | Design direction supplied here | Normative detail deferred |
|---|---|---|
| Clone/migration/restore/replacement/fresh definitions | Use explicit semantic categories rather than hardware inference | Exact definitions and boundaries |
| Classification authority | Explicit authorized declaration is preferred | Actor/role, authentication and delegation |
| Minimum evidence and timing | Declaration plus protected lineage is preferred | Required fields, timing and freshness |
| Automatic versus explicit classification | Automation may corroborate but not silently create intent | Exact automatic/explicit boundary |
| Missing/conflicting/stale evidence | Conservative ambiguity gate is preferred | Exact state, output and recovery |
| Concurrent-use evidence | Bounded corroboration only | Sources, confidence and conflict effect |
| Scope/secret/reference/observation effects | Governed by selected classification and accepted CA-001 | Complete transition matrix |
| Scope versus secret rotation coupling | No decision in synthesis | Coupled/separate cases and order |
| Atomic transition boundary | Preserve CA-001 snapshot atomicity | Transaction/provenance requirements |
| Audit/provenance | Protected lineage is preferred | Schema, retention, privacy and integrity |
| Accidental clone/incomplete migration recovery | Requires explicit recovery path | States, authority and allowed transitions |
| Air-gap/split-brain treatment | Must not depend on mandatory online proof | Exact offline declaration/gate behavior |
| Historical lineage | Preserve discontinuity without identity aliasing | Representation and retention |
| Failure classification | Conservative gate direction | Exact authorized error/outcome mapping |

## Candidate-strategy evaluation

Disposition values are exactly `REJECT`, `ACCEPTABLE_COMPONENT` or
`CANNOT_STAND_ALONE`. `ACCEPTABLE_COMPONENT` does not mean a complete or
normative rule; it means the concept can participate in the recommended design.

### Strategy A — Explicit authorized transition declaration

**Disposition: ACCEPTABLE_COMPONENT**

| Dimension | Assessment |
|---|---|
| Strengths | Expresses logical intent directly; works offline; distinguishes migration/separation conceptually; highly traceable. |
| Weaknesses | Does not itself prove source retirement or prevent conflicting declarations. |
| Risks | Wrong, replayed, stale or unauthorized declaration could preserve or split identity incorrectly. |
| DF-002 compatibility | Potentially strong because deterministic intent can preserve continuity/separation without hardware identity. |
| CA-001 compatibility | Strong if declaration only selects an explicitly governed identity transition and never alters cryptographic constants. |
| Implementation complexity | MEDIUM; authority, authentication, persistence and conflict handling remain unspecified. |
| Reviewability | HIGH when declaration semantics and evidence are explicit. |
| Deterministic behavior | Potentially HIGH for valid declarations; conflict/absence behavior still needed. |
| Privacy impact | Can avoid machine-derived identity; declaration metadata still requires minimization. |
| Operational impact | Requires an explicit workflow at copy/restore/migration boundaries. |

Technical justification: intent cannot be derived from HMAC state, host state or
copy mechanics. An explicit authority path is therefore a reasonable component,
but it needs lineage and an ambiguity gate to handle proof and failure.

### Strategy B — Protected lineage/provenance state

**Disposition: ACCEPTABLE_COMPONENT**

| Dimension | Assessment |
|---|---|
| Strengths | Durable traceability across creation, backup, restore, migration and generations; supports fork/rollback analysis. |
| Weaknesses | Copied lineage can repeat the same claim; provenance does not itself express current intent or source retirement. |
| Risks | Replay, corruption, partial restore, unbounded retention and sensitive operational metadata. |
| DF-002 compatibility | Potentially strong if private, deterministic and excluded from public artifacts. |
| CA-001 compatibility | Strong; CA-001 already permits private generation/snapshot provenance and requires private collision state. |
| Implementation complexity | MEDIUM/HIGH; schema, integrity, atomicity, retention and recovery are open. |
| Reviewability | HIGH if a later specification makes events, precedence and retention exact. |
| Deterministic behavior | Potentially HIGH for valid lineage; copied/conflicting lineage needs a gate. |
| Privacy impact | Private sensitive metadata; export/log prohibition and minimization are necessary. |
| Operational impact | Backup/migration workflows need to preserve or deliberately branch lineage. |

Technical justification: lineage supplies durable evidence missing from a bare
declaration, but it cannot stand as sole intent authority. It is a core
component of the preferred combination.

### Strategy C — Deployment/platform operation attestation

**Disposition: ACCEPTABLE_COMPONENT**

| Dimension | Assessment |
|---|---|
| Strengths | Captures clone/move/restore/image operations near their source; useful in managed environments. |
| Weaknesses | Platform-specific, optional and often absent after export/import. |
| Risks | Operation label may not match logical intent; vendor semantics and trust vary. |
| DF-002 compatibility | Compatible only as optional evidence, not as a required platform-dependent identity root. |
| CA-001 compatibility | Orthogonal when it does not enter HMAC inputs or select cryptographic parameters. |
| Implementation complexity | HIGH across heterogeneous VM, LXC, container and backup systems. |
| Reviewability | MEDIUM; adapters and source semantics multiply review surface. |
| Deterministic behavior | LOW/MEDIUM alone; improved only when normalized under explicit precedence. |
| Privacy impact | Can expose host/infrastructure identifiers; strict minimization would be required. |
| Operational impact | Valuable for automation but unavailable in local/manual and air-gapped cases. |

Technical justification: the evidence can corroborate declaration/lineage, but
platform operation type cannot independently decide logical installation
identity.

### Strategy D — Active uniqueness/lease coordination

**Disposition: CANNOT_STAND_ALONE**

| Dimension | Assessment |
|---|---|
| Strengths | May detect concurrent use and split-brain while connected. |
| Weaknesses | Cannot prove uniqueness under partition, delay or air gap. |
| Risks | Availability coupling, false confidence from absent conflicts and new coordination ownership semantics. |
| DF-002 compatibility | Weak if mandatory; potentially compatible as optional evidence only. |
| CA-001 compatibility | Does not change derivation, but a mandatory network dependency would conflict with local/offline posture. |
| Implementation complexity | HIGH; lease service, failure recovery, clocks/ordering and partitions. |
| Reviewability | MEDIUM/LOW because distributed failure modes are broad. |
| Deterministic behavior | LOW alone under partitions; deterministic interpretation rules would still be needed. |
| Privacy impact | Coordination identifiers/activity can enable correlation. |
| Operational impact | Adds service availability and air-gap limitations. |

Technical justification: concurrency evidence can be corroborative, but no
online mechanism can be the sole classifier for offline-capable architecture.

### Strategy E — Conservative unknown-state gate

**Disposition: ACCEPTABLE_COMPONENT**

| Dimension | Assessment |
|---|---|
| Strengths | Prevents weak evidence from silently preserving or rotating identity; aligns with ambiguity/fail-closed governance. |
| Weaknesses | Can reduce availability for legitimate recovery and migration. |
| Risks | An overbroad gate can make recovery operationally impractical; an underdefined gate recreates implementation variance. |
| DF-002 compatibility | Strong safety fit when bounded to affected identity capability and explicit stale behavior. |
| CA-001 compatibility | Strong conceptual fit with fail-closed secret/collision behavior; exact clone outcome is still separate. |
| Implementation complexity | MEDIUM; evidence thresholds, state and recovery authority remain open. |
| Reviewability | HIGH if entry/exit conditions and effects are closed and explicit. |
| Deterministic behavior | Potentially HIGH; exact precedence is required. |
| Privacy impact | Avoids disclosure-based troubleshooting; bounded status can remain non-sensitive. |
| Operational impact | Requires an authorized resolution path and may pause publication. |

Technical justification: declaration and lineage can be absent or conflicting.
The architecture therefore needs a component that refuses to infer intent, but
this record does not define the resulting state.

### Strategy F — Always preserve copied identity state

**Disposition: REJECT**

| Dimension | Assessment |
|---|---|
| Strengths | Simple; maximizes continuity; reproduces bytes after restore. |
| Weaknesses | Cannot distinguish move from multiple active descendants. |
| Risks | Cross-installation correlation, duplicate publication and silent shared identity. |
| DF-002 compatibility | Incompatible for copies that are distinct installations. |
| CA-001 compatibility | Cryptographically reproducible but violates the prohibition on secret reuse across distinct installations. |
| Implementation complexity | LOW. |
| Reviewability | HIGH but incorrect for the full scenario set. |
| Deterministic behavior | HIGH mechanically; semantically wrong for distinct copies. |
| Privacy impact | High correlation risk. |
| Operational impact | Easy restore, unsafe cloning and test-copy behavior. |

Technical justification: deterministic simplicity does not satisfy the frozen
separation requirement and does not close R003-F-002.

### Strategy G — Always rotate after copy/restore evidence

**Disposition: REJECT**

| Dimension | Assessment |
|---|---|
| Strengths | Separates detected copies without needing intent. |
| Weaknesses | Treats valid restore, replacement and migration as new identity. |
| Risks | Silent historical discontinuity, false rotation and loss of stable joins. |
| DF-002 compatibility | Incompatible with authorized continuity expectations. |
| CA-001 compatibility | Conflicts with CA-001's prohibition on automatic ordinary-restore rotation. |
| Implementation complexity | LOW/MEDIUM; copy detection itself remains unreliable. |
| Reviewability | HIGH but incorrect for legitimate continuity cases. |
| Deterministic behavior | Only as deterministic as incomplete operation evidence. |
| Privacy impact | Separates contexts but can cause unnecessary churn and lineage exposure. |
| Operational impact | Damages disaster recovery and migration continuity. |

Technical justification: universal rotation solves one risk by violating an
accepted lifecycle constraint and therefore cannot be retained.

### Strategy H — Environmental fingerprint classification

**Disposition: REJECT**

| Dimension | Assessment |
|---|---|
| Strengths | Locally observable; superficially easy to automate. |
| Weaknesses | Mutable, spoofable, virtualized, copied and unrelated to logical intent. |
| Risks | False clone decisions during maintenance and false continuity for copied environments. |
| DF-002 compatibility | Weak; undermines stable logical identity and privacy boundaries. |
| CA-001 compatibility | Incompatible as identity authority because host/address/machine data are excluded from derivation semantics. |
| Implementation complexity | MEDIUM across platforms despite weak assurance. |
| Reviewability | LOW because signal meaning varies by environment. |
| Deterministic behavior | LOW across hardware/virtualization changes. |
| Privacy impact | Introduces potentially sensitive and correlatable infrastructure data. |
| Operational impact | Fragile under repair, migration, rescheduling and network changes. |

Technical justification: environmental attributes can be contextual diagnostics
but cannot become authoritative clone identity under inherited constraints.

## Disposition summary

| Strategy | Disposition | Role in recommended direction |
|---|---|---|
| A Explicit declaration | ACCEPTABLE_COMPONENT | Primary expression of intent |
| B Protected lineage | ACCEPTABLE_COMPONENT | Durable supporting evidence and transition history |
| C Platform attestation | ACCEPTABLE_COMPONENT | Optional corroborating operation evidence |
| D Active coordination | CANNOT_STAND_ALONE | Optional corroborating concurrency evidence only |
| E Conservative unknown gate | ACCEPTABLE_COMPONENT | Safety boundary for insufficient/conflicting evidence |
| F Always preserve | REJECT | Violates distinct-installation separation |
| G Always rotate | REJECT | Violates valid restore/migration continuity |
| H Environmental fingerprint | REJECT | Unreliable and privacy-incompatible as authority |

## One strategy versus combination

**A combination is preferred.**

No single strategy covers all required evidence conditions:

- declaration expresses intent but cannot prove lineage or source retirement;
- lineage preserves history but can itself be copied;
- an ambiguity gate prevents unsupported inference but cannot supply intent;
- platform evidence can corroborate operations but is not portable;
- concurrency evidence can reveal some conflicts but cannot exclude air-gapped
  duplicates.

The preferred architecture shape therefore combines A + B + E as its conceptual
core, with C and D available only as bounded corroborating evidence. The
combination is preferred because each core component addresses a different
failure mode: intent, durable provenance and unresolved ambiguity. None may be
silently substituted by hardware/environment inference.

This is design rationale, not precedence, state-machine or output semantics.
Batch 1B still needs exact authority, evidence, conflict and transition rules.

## Architecture Decision Summary

### Recommended architecture

A composite declaration-and-lineage architecture with a conservative ambiguity
gate is recommended for Batch 1B design:

- explicit authorized declaration represents logical-installation intent;
- protected private lineage provides durable transition evidence;
- insufficient or conflicting evidence enters an explicit ambiguity path rather
  than being inferred;
- platform and active-concurrency signals are corroborative only;
- always-preserve, always-rotate and environmental-fingerprint classification
  are excluded from the future design.

### Remaining unresolved questions

1. Which actor/component is authorized to declare continuity or separation?
2. How is declaration authority authenticated, scoped, revoked and audited?
3. What exact private lineage fields, integrity properties and retention apply?
4. What evidence establishes source retirement or a legitimate fork?
5. What exact state results from missing, stale, conflicting or replayed evidence?
6. How are air-gapped and partitioned duplicates handled without online proof?
7. Which scope/secret-generation combinations preserve versus change identity?
8. Are scope and secret transitions coupled, and in what order?
9. How is accidental-clone recovery authorized without silent aliasing?
10. What non-secret historical lineage may be retained after separation?
11. What bounded role, if any, can platform/concurrency evidence play in raising
    or resolving an ambiguity?
12. Which exact lifecycle outcomes map to the frozen outcome vocabulary?

### Assumptions that must NOT be made

- Copied scope/secret state proves intended continuity.
- A different host, VM ID, container ID, hostname, MAC address, IP address,
  machine ID, CPU, NIC or motherboard proves a new installation.
- Absence of concurrent activity proves uniqueness.
- A restore is always a migration or always a clone.
- Missing identity state proves a fresh installation.
- Platform operation labels are universally available or semantically uniform.
- Operator intent is authoritative without a defined authority and evidence path.
- Secret rotation alone can silently resolve clone identity.
- Historical and new public identities may be aliased because raw source data is
  equal.
- Implementation may choose behavior for an unresolved gate.

### Information still missing

- authoritative declaration role and trust boundary;
- declaration/provenance representation and integrity model;
- exact source-retirement and fork evidence;
- offline conflict-resolution evidence;
- safe ambiguity outcome and recovery path;
- exact scope/secret transition matrix;
- private lineage retention/minimization boundary;
- mapping to lifecycle and error outcomes;
- affected normative vectors and audit evidence.

### Mandatory ambiguity gates retained for Batch 1B

- unknown or conflicting classification authority;
- missing, corrupt, replayed or contradictory lineage;
- copy versus move without source-disposition evidence;
- restore versus fork with possible active descendants;
- air-gapped or partitioned uniqueness uncertainty;
- prior identity state missing with evidence of prior existence;
- unauthorized secret regeneration or unexplained generation change;
- disagreement between declaration, lineage and optional platform/concurrency
  evidence.

The record intentionally does not define what these gates emit or how they are
resolved.

## Validation conclusion

- Candidate strategies evaluated: 8 of 8.
- Batch 1A ambiguities addressed: 10 of 10.
- Batch 1A decision areas addressed: 14 of 14.
- Preferred design: combination, with technical rationale.
- Normative clone rules created: 0.
- Implementation authorized: no.

**DECISION_SYNTHESIS_COMPLETE_NON_NORMATIVE**

