# AI-002 Architecture Consistency Review

## Review status

**FAIL**

This is a review-only artifact. It does not amend, reinterpret, repair or
supersede any reviewed document. It introduces no requirement and authorizes no
implementation.

## Governance and scope

AI-002 is the sole active authority. CA-001 is `ACCEPTED`; DF-002 remains the
active implementation baseline; `hadocs-generic-metadata 1.0.0` remains the
active contract; implementation, contract activation and DF-003 remain
prohibited.

Reviewed inputs:

1. `AI-002_CLONE_IDENTITY_SPECIFICATION.md`
2. `AI-002_RELATIONSHIP_REFERENCE_CORRECTION.md`
3. `AI-002_REMOVAL_SEMANTICS.md`
4. `AI-002_VERSION_COMPATIBILITY.md`
5. all accepted CA-001 architecture documents, with particular attention to
   the normative specification, secret lifecycle, migration/recovery and test
   vectors
6. DF-002

Review dimensions were limited to terminology, lifecycle states, version
terminology, identity terminology, relationship terminology, fail-closed
behavior, `UNKNOWN`, CA-001/DF-002 references, prohibited behavior, decision
tables and traceability.

## Method

The review compared:

- each defined term and closed vocabulary;
- every normative state/result pair;
- narrative transition rules against deterministic tables;
- each use of `UNKNOWN` and fail-closed consequences;
- identity-context, installation-scope, secret-generation and reference terms;
- relationship creation, absence, invalidity, recreation and discontinuity;
- architecture, contract, implementation and document version dimensions;
- every inherited-authority and traceability statement; and
- prohibited aliases, fallbacks, inference and public disclosure.

No input was changed.

## Findings

### AICR-F-001 — Removal transition conflicts with its lifecycle matrix

**Classification:** normative inconsistency  
**Result impact:** FAIL

Affected document: `AI-002_REMOVAL_SEMANTICS.md`.

Section 4.2 states that a prior `REMOVED` identity followed by a successful
collection in which the object remains absent stays `REMOVED` **only if** the
prior authoritative removal remains applicable. Section 10.3 gives the same
prior state and `Complete absent` input the unconditional result `REMOVED`.

The conditional narrative and unconditional matrix do not define identical
behavior. The narrative does not state the outcome when the prior signal is no
longer applicable, while the matrix does. Consequently:

- the removal lifecycle is not closed by one identical rule;
- the narrative and deterministic table disagree; and
- an independent implementation would have to choose which statement controls.

This review records the inconsistency only. It does not select an outcome or
propose corrected wording.

### AICR-O-001 — `UNKNOWN` is a shared token with domain-specific meanings

**Classification:** observation; no independent contradiction

The Clone Identity Specification defines `UNKNOWN` as a clone-classification
result when authoritative lineage/classification evidence is insufficient. The
Version Compatibility document defines `UNKNOWN` as a compatibility result
when version/support evidence is unavailable, malformed, contradictory or
unverifiable. Removal Semantics does not make `UNKNOWN` a lifecycle state; it
consumes Clone Identity `UNKNOWN + FAIL_CLOSED` and otherwise uses
`UNAVAILABLE` for inability to determine current source presence.

The uses are explicitly domain-scoped and share the same no-inference,
fail-closed safety posture. They are therefore behaviorally compatible, but the
token does not have one identical cross-document semantic type. This is an
observation only; the review does not rename or unify the terms.

### AICR-O-002 — Fail-closed behavior is consistent but expressed at different layers

**Classification:** observation; no independent contradiction

The reviewed documents express fail-closed outcomes using different
layer-specific labels:

- Clone Identity: `FAIL_CLOSED` activation outcome;
- Relationship Reference: `CAPABILITY_FAIL_CLOSED` and no new relationship set;
- Removal Semantics: lifecycle not advanced, no new current identity conclusion,
  and optional retention of the last valid stale snapshot;
- Version Compatibility: no current interpretation, join, migration or emission;
  historical retention remains separately permitted;
- CA-001: reject the affected derivation/capability without fallback or secret/raw
  identifier exposure.

Their normative safety consequences agree: no new identity-dependent current
output, no fallback or inference, and no retroactive invalidation of valid
immutable history. The vocabulary is not textually identical because each term
belongs to a different result layer. This review records the distinction and
makes no normalization change.

## Consistency matrix

| Review dimension | Result | Evidence summary |
|---|---|---|
| General terminology | PASS WITH OBSERVATION | Defined terms are scoped; `UNKNOWN` is overloaded across two result domains. |
| Lifecycle states | FAIL | Section 4.2 and Section 10.3 of Removal Semantics disagree for `REMOVED` plus complete absence. |
| Version terminology | PASS | Architecture, contract, implementation and document versions remain independent; active 1.0.0 and proposed inactive 2.0.0 are distinguished. |
| Identity terminology | PASS | Logical installation, identity context, installation scope, secret generation, public reference and observation identity are used consistently. |
| Relationship terminology | PASS | `source_ref`, `target_ref`, relationship tuple, `CURRENT_ABSENT`, invalidity, recreation and replacement retain their defined meanings. |
| Fail-closed behavior | PASS WITH OBSERVATION | Safety behavior agrees; layer-specific result labels differ. |
| `UNKNOWN` semantics | PASS WITH OBSERVATION | Both uses prohibit inference and fail closed, but represent different domain result types. |
| CA-001 references | PASS | HMAC-SHA-256, exact 32-octet secret, `refh1_`, format version 1, context/collision rules and historical preservation are not redefined. |
| DF-002 references | PASS | DF-002 remains baseline; contract 1.0.0, four capabilities, four categories and four predicates remain unchanged. |
| Prohibited behavior | PASS | No alias, raw-ID/secret exposure, fallback, hardware identity, silent regeneration, cross-context resurrection or contract activation is permitted. |
| Decision-table agreement | FAIL | AICR-F-001 prevents agreement. Other reviewed cross-document transitions align. |
| Traceability references | PASS | C-002 through C-005 trace to DF-002, AI-001, R-003, accepted CA-001 and preceding AI-002 corrections without changing their authority roles. |

## Cross-document agreements

The review confirmed the following shared rules:

- `SAME_LOGICAL_INSTALLATION + PRESERVE_CONTEXT` preserves the CA-001 identity
  context when all identity inputs remain equal.
- `DISTINCT_LOGICAL_INSTALLATION + NEW_CONTEXT_REQUIRED` prohibits aliasing and
  requires a separate context before new publication.
- `UNKNOWN + FAIL_CLOSED` produces no new identity-dependent current output.
- A CA-001 failure never falls back to raw identifiers, unkeyed derivation,
  another secret, another prefix or another format.
- `source_ref` is exactly the validated `refh1_entity_` reference and is not an
  `obs1_` observation ID.
- Relationship absence does not remove or invalidate either endpoint.
- `IDENTITY_INVALID` is reserved for present or attempted invalid identity
  input; it is not ordinary absence or unavailability.
- Historical references retain original bytes and context and cannot be
  rewritten, aliased or resurrected across context or contract-major changes.
- Contract major 1 and the proposed, inactive major 2 current surfaces are not
  compatible or mixable.
- DF-002 remains active and none of the reviewed documents activates DF-003,
  implementation or a new contract.

## Traceability review

| Correction | Primary document | Reviewed inherited chain | Result |
|---|---|---|---|
| C-001 | accepted CA-001 package | DF-002 → R003-F-001 → CA-001 → R-004 verification | PASS |
| C-002 | Clone Identity Specification | DF-002 → AI-001 → R003-F-002 → accepted CA-001 | PASS |
| C-003 | Relationship Reference Correction | DF-002 → AI-001 → R003-F-003 → CA-001 → C-002 | PASS |
| C-004 | Removal Semantics | DF-002 → AI-001 → R003-F-004 → CA-001 → C-002 → C-003 | FAIL: internal lifecycle inconsistency AICR-F-001 |
| C-005 | Version Compatibility | frozen Version Strategy → AI-001 → R003-F-005 → CA-001 → C-002/C-003/C-004 | PASS subject to unresolved C-004 consistency failure |

## Review conclusion

The architecture package does not pass complete cross-document consistency
because AICR-F-001 leaves two non-identical normative outcomes for one removal
transition. The two observations do not independently affect correctness, but
they should remain visible to a later governed disposition because the review
criteria requested identical terminology and `UNKNOWN` semantics.

No correction is made here. No new requirement, architecture, contract,
implementation, test, fixture, governance record or Design Freeze is created.

**FAIL**
