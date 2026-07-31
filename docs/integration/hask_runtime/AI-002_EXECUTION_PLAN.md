# AI-002 Re-baselined Execution Plan

## Purpose and status

This plan reconstructs AI-002 from repository authority after formal acceptance
of CA-001. It is an inventory and execution plan only. It does not define the
remaining correction semantics, change a contract, create DF-003 or authorize
implementation.

AI-002 is the sole active authority. DF-002 remains the implementation baseline
and `hadocs-generic-metadata 1.0.0` remains the active contract. Implementation
is prohibited.

## Inherited authorities

| Authority | Current effect on AI-002 |
|---|---|
| G-001 | Architecture precedes implementation; ambiguity blocks; independent review and Design Freeze remain mandatory. |
| G-002 | Repository state controls resume; complete artifacts are preserved and never recreated. |
| PS-001 | Program-status vocabulary and navigation remain informational, not architecture authority. |
| DF-002 | Active implementation baseline; four capabilities, four observation categories, four predicates and contract 1.0.0 remain frozen. |
| AI-001 | Immutable base proposal. Unaffected canonical-key, source-capability and observation-ID rules remain frozen for AI-002. |
| R-003 | Sole source of the five AI-002 correction findings and the major-version requirement. |
| CA-001 | ACCEPTED cryptographic architecture for C-001/R003-F-001. It is normative input and read-only. |
| R-004 | VERIFIED review evidence for CA-001 after its correction cycle. |
| CA-001-FIX-001 | COMPLETE correction evidence for collision scope, secret wording and scope vector. |
| R-004-VERIFY | COMPLETE independent verification evidence; all three R-004 findings resolved. |
| AI-002 active authority | Permits only the five R-003 correction areas and associated implementation-planning documentation. |

## Objective inventory

### Five correction objectives

| Objective | Current classification | Repository basis | Remaining AI-002 action |
|---|---|---|---|
| C-001 / R003-F-001 — secret local material and reference hashing | **COMPLETE_BY_ACCEPTED_CA001** | CA-001 ACCEPTED; R-004 VERIFIED; all vectors pass | Incorporate CA-001 by normative reference into combined AI-002 traceability, byte-impact, privacy, stability and category-impact documents. Do not redesign it. |
| C-002 / R003-F-002 — clone identity and rotation | **REMAINING** | Only requirements exist; CA-001 explicitly leaves clone classification outside its scope | Define clone/non-clone cases, authoritative classifier/evidence, safe unknown outcome, secret/scope rotation and concurrent-clone behavior. |
| C-003 / R003-F-003 — relationship `source_ref` | **REMAINING** | R-003 conflict remains; CA-001 defines `refh1_` but does not adopt relationship semantics | Define exactly one source-reference representation and its relationship to observation ID, accepted opaque references, validation, migration and relationship IDs. |
| C-004 / R003-F-004 — removal versus `IDENTITY_INVALID` | **REMAINING** | R-003 ambiguity remains | Define removal, absence, unavailable inputs, malformed identity, secret failure, collision and recreation outcomes without invalidating historical identity. |
| C-005 / R003-F-005 — contract major version | **REMAINING** | R-003 requires `INCREMENT_MAJOR_VERSION`; active version remains 1.0.0 | Propose exact successor major version and compatibility/coexistence treatment after all byte and semantic impacts are known; do not activate it. |

### Cross-cutting objectives

| Objective | Classification | Remaining action |
|---|---|---|
| Preserve frozen AI-001 surface | **COMPLETE_AS_BASELINE; CONTINUOUS_GATE** | Recheck every batch against `AI-002_FROZEN_AI001_INVENTORY.md`. |
| Five-finding traceability | **COMPLETE_FOR_PREFLIGHT; CLOSURE_REMAINING** | Preserve the preflight register; publish final closure matrix in the combined amendment/review package rather than rewriting the complete preflight artifact. |
| Normative vectors | **PARTIAL** | CA-001 vectors close the cryptographic portion. Add or update only vectors affected by clone, source-reference, removal and major-version corrections. Preserve unaffected AI-001 vectors byte-for-byte. |
| Stability matrix amendment | **REMAINING** | Cover every lifecycle event and map outcomes to the authorized closed vocabulary. |
| Privacy amendment | **REMAINING** | Incorporate accepted CA-001 plus clone and source-reference privacy consequences. |
| Category impact | **REMAINING** | Record impact for all four Release 1 categories without changing counts or names. |
| Consolidated architecture amendment | **REMAINING** | Establish precedence over only the five defective AI-001 statements and preserve everything else. |
| Independent-review package | **REMAINING** | Produce five-finding closure, byte/privacy/stability/version matrices, vectors and exact approval/rejection criteria. AI-002 cannot self-approve. |
| Final report/state | **REMAINING** | Generate only after all five findings are CLOSED or CLOSED_WITH_NOTES and deterministic validation passes twice. |

## Existing deliverable classification

| Deliverable | Classification | Treatment |
|---|---|---|
| `AI-002_BASELINE_VERIFICATION.md` | COMPLETE | Preserve; its historical pre-CA status is supplemented by resumption records. |
| `AI-002_AUTHORIZED_SCOPE.md` | COMPLETE | Preserve as the five-finding boundary. |
| `AI-002_R003_FINDINGS_TRACEABILITY.md` | COMPLETE_FOR_PREFLIGHT | Preserve; NOT_ADDRESSED values are historical pre-correction state, not current closure status. |
| `AI-002_FROZEN_AI001_INVENTORY.md` | COMPLETE | Preserve and use as continuous regression gate. |
| `AI-002_REFERENCE_HASH_COMPATIBILITY.md` | SUPERSEDED_AS_ACTIVE_CONCLUSION | Preserve as evidence of the former authority gap; CA-001 now supplies the accepted construction. Do not recreate or edit. |
| `AI-002_SECRET_LOCAL_MATERIAL_SPECIFICATION.md` | SUPERSEDED_AS_ACTIVE_CONCLUSION | Preserve as the maximum pre-CA reconstruction; accepted CA-001 supplies the formerly missing normative fields. Do not recreate or edit. |
| `AI-002_BLOCKER_REPORT.md` | OBSOLETE_FOR_CURRENT_STATUS; HISTORICAL | Preserve; the recorded cryptographic blocker was resolved by CA-001 and its review chain. |
| `AI-002_BLOCKER_STATE.json` | OBSOLETE_FOR_CURRENT_STATUS; HISTORICAL | Preserve unchanged; active governance state supersedes it. |
| `AI-002_RESUMPTION_STATUS.md` | COMPLETE | Current resumption bridge and planning boundary. |
| `AI-002_EXECUTION_PLAN.md` | CREATED_BY_THIS_BATCH | Current deterministic remainder plan. |
| `AI-002_CLONE_ANALYSIS.md` | MISSING | Create in Batch 1A; inventory scenarios, evidence, ambiguity gates, decision requirements and reasonable alternatives without making normative decisions. |
| `AI-002_CLONE_IDENTITY_SPECIFICATION.md` | MISSING | Create in Batch 1B after Clone Analysis is complete. |
| `AI-002_RELATIONSHIP_REFERENCE_CORRECTION.md` | MISSING | Create in Batch 2. |
| `AI-002_REMOVAL_SEMANTICS_CORRECTION.md` | MISSING | Create in Batch 3. |
| `AI-002_VERSIONING_COMPATIBILITY.md` | MISSING | Create in Batch 4. |
| `AI-002_STABILITY_MATRIX_AMENDMENT.md` | MISSING | Create in Batch 5. |
| `AI-002_PRIVACY_AMENDMENT.md` | MISSING | Create in Batch 5. |
| `AI-002_CATEGORY_PROFILE_IMPACT.md` | MISSING | Create in Batch 5. |
| `AI-002_ARCHITECTURE_AMENDMENT.md` | MISSING | Create in Batch 6. |
| `AI-002_R004_REVIEW_PACKAGE.md` | MISSING | Create in Batch 6. |
| `AI-002_FINAL_REPORT.md` | MISSING | Create in Batch 7 after review-readiness validation. |
| `AI-002_FINAL_STATE.json` | MISSING | Create in Batch 7 and validate deterministically. |
| `AI-002_OUT_OF_SCOPE_ISSUES.md` | CONDITIONAL | Create only if a genuine unrelated issue is found; none is established by this re-baseline. |

## Superseded work

CA-001 supersedes only the active conclusions that the cryptographic primitive,
secret representation, framing, lifecycle and vectors are undetermined. It does
not erase the historical blocker documents and does not supersede their valid
reconstruction of inherited DF-002 requirements.

The following work must not be repeated:

- selecting or comparing cryptographic primitives;
- defining secret length, encoding, generation, backup, loss or rotation rules;
- defining HMAC domain/framing/output bytes;
- defining cryptographic collision-detection scope;
- regenerating CA-001 test vectors;
- independently reviewing CA-001 again.

AI-002 consumes the accepted result by reference.

## Remaining architecture ambiguities and blockers

### Known unresolved architecture work

1. **Clone authority (highest risk):** the authoritative classifier, evidence
   and safe result when clone status is unknown are not yet defined. CA-001
   deliberately left this to C-002.
2. **Relationship endpoint semantics:** the exact `source_ref` representation
   after accepted `refh1_` derivation and its relation to `obs1_` remain open.
3. **Removal-state partition:** ordinary absence, unavailable identity input,
   malformed identity and collision failure remain to be separated.
4. **Successor contract proposal:** the exact major version and namespace/schema
   consequences remain open until C-002 through C-004 byte impacts are fixed.

These are authorized AI-002 decision surfaces, not permission for
implementation to choose. The re-baseline found no new out-of-scope defect and
no proof yet that an authorized correction is impossible. Each batch must still
apply AI-002's ambiguity stop rule; C-002 is the most likely blocker gate if
authoritative classification evidence cannot uniquely support a rule.

### Blockers before DF-003

- C-002 through C-005 are not closed.
- C-001 has not yet been integrated into the combined AI-002 amendment and
  impact matrices.
- Required lifecycle, privacy, category and version impacts are incomplete.
- The complete amended architecture lacks an independent-review package and
  later independent approval.
- AI-002 final status and deterministic final state do not exist.
- DF-003 has no authority and cannot be created by AI-002.

## Dependency graph

```text
Accepted CA-001 / C-001
        |
        v
Batch 1A: clone analysis (non-normative)
        |
        v
Batch 1B: C-002 clone identity specification
        |
        +--> Batch 2: C-003 source_ref
        |
        +--> Batch 3: C-004 removal semantics
                     |
        +------------+
                     v
         Batch 4: C-005 version proposal
                     |
                     v
   Batch 5: stability + privacy + category impact
                     |
                     v
   Batch 6: consolidated amendment + review package
                     |
                     v
      Batch 7: final report/state + validation
                     |
                     v
     separate independent review authority
                     |
                     v
            separate DF-003 authority
```

## Prioritized execution order

### Batch 1A — Clone Analysis

Create `AI-002_CLONE_ANALYSIS.md`. Inventory every clone, restore, migration,
host-replacement, staging/test-copy and concurrent-copy scenario required by
AI-002. Inventory available authoritative evidence, identify ambiguity gates,
identify the architecture decisions that a later specification must make and
compare technically reasonable alternatives against inherited constraints.

Batch 1A is analysis only. It makes no normative clone classification, rotation,
identity-continuity or failure decision. If evidence cannot support the later
decision boundary, record the blocker rather than selecting an alternative.

### Batch 1B — Clone Identity Specification

Consume the completed `AI-002_CLONE_ANALYSIS.md` and create
`AI-002_CLONE_IDENTITY_SPECIFICATION.md`. Resolve C-002 before other
cross-system impacts because clone classification controls secret, scope,
reference and observation continuity. Every normative rule must trace to the
analysis and inherited authority. Stop if authoritative classification cannot
be defined without guessing.

### Batch 2 — Relationship reference correction

Create `AI-002_RELATIONSHIP_REFERENCE_CORRECTION.md`. Consume accepted CA-001
and the completed clone decision. Define one public `source_ref`, validation,
relationship-ID impact and migration boundary without adding predicates.

### Batch 3 — Removal semantics

Create `AI-002_REMOVAL_SEMANTICS_CORRECTION.md`. Separate ordinary absence,
temporary unavailability, permanent malformed identity, secret failure,
collision and recreation. Preserve historical identity.

### Batch 4 — Version compatibility

Create `AI-002_VERSIONING_COMPATIBILITY.md`. After byte/semantic effects are
known, propose the exact successor major version and coexistence/deprecation
rules. Do not activate it.

### Batch 5 — Cross-cutting impact set

Create the stability-matrix, privacy and category-impact amendments together.
This batch integrates C-001 through C-005 across all four categories and checks
the frozen AI-001 inventory.

### Batch 6 — Consolidated amendment and independent-review package

Create `AI-002_ARCHITECTURE_AMENDMENT.md` and
`AI-002_R004_REVIEW_PACKAGE.md`. Include the five-finding closure matrix,
unchanged-rule inventory, byte/privacy/stability/version impacts and only the
vectors affected by corrections.

### Batch 7 — Completion and deterministic validation

Create `AI-002_FINAL_REPORT.md` and `AI-002_FINAL_STATE.json`; validate JSON,
internal consistency, five-of-five closure, unchanged counts/scope, prohibited
surface preservation and two-pass deterministic hashes. Successful completion
only establishes readiness for a separately activated independent review.

## Batch estimate

**Eight remaining AI-002 execution batches** are recommended after this
sequencing refinement: Batch 1A, Batch 1B and Batches 2 through 7. The estimate
separates non-normative clone analysis from the normative clone specification
while preserving one normative dependency boundary per later batch.
It may decrease only if two adjacent documents prove mechanically coupled; it
must increase or stop if an ambiguity gate or out-of-scope defect is triggered.

## DF-003 readiness

**NOT_READY_FOR_DF003**

CA-001 removes the cryptographic authority blocker, but AI-002 has not closed
C-002 through C-005, produced its cross-cutting amendments, completed the
five-finding review package or received independent approval of the combined
architecture. DF-002 therefore remains the implementation baseline.

Readiness progression:

```text
READY_FOR_AI002_EXECUTION
NOT_READY_FOR_INDEPENDENT_COMBINED_REVIEW
NOT_READY_FOR_DF003
NOT_READY_FOR_IMPLEMENTATION
```
