# AI-002 Architecture Consistency Correction

## Authority and scope

This Batch 5A record is authorized only to correct AICR-F-001 and disposition
AICR-O-001 and AICR-O-002 from
`AI-002_ARCHITECTURE_CONSISTENCY_REVIEW.md`.

AI-002 remains the sole active authority. CA-001 remains `ACCEPTED`; DF-002
remains the active implementation baseline; `hadocs-generic-metadata 1.0.0`
remains the active contract; implementation remains prohibited.

This record does not redesign clone identity, relationship references, removal
states, version compatibility or CA-001. It does not introduce a new normative
value, transition, requirement or implementation behavior.

## AICR-F-001 root cause

Removal Semantics Section 4.2 and Section 10.3 described one event using two
non-identical formulations:

- Section 4.2 made retention of `REMOVED` conditional on the prior removal
  signal remaining applicable.
- Section 10.3 unconditionally returned `REMOVED` for prior state `REMOVED`
  plus `Complete absent`.

The conditional phrase did not define an alternative result. It therefore left
an implementation choice despite the otherwise closed lifecycle matrix.

## Exact correction

Only the Section 4.2 transition row was changed.

### Before

```text
REMOVED + object remains absent in successful collection
→ REMOVED
→ remain absent only if prior authoritative removal remains applicable
```

### After

```text
REMOVED + object remains absent in successful collection
→ REMOVED
→ remain absent; continued absence alone does not create a new classification
```

The corrected prose now exactly matches Section 10.3:

```text
prior REMOVED + Complete absent → REMOVED
```

A transition out of `REMOVED` continues to require a separately defined,
positively evidenced event. The existing valid-recreation/reappearance row
returns `ACTIVE`; unavailable collection returns `UNAVAILABLE`; invalid present
identity returns `IDENTITY_INVALID`. Elapsed time, repeated scans and continued
absence do not independently change classification.

## Affected sections and tables

| Artifact | Location | Disposition |
|---|---|---|
| `AI-002_REMOVAL_SEMANTICS.md` | Section 4.2, `REMOVED` plus successful continued absence row | one consequence phrase corrected |
| `AI-002_REMOVAL_SEMANTICS.md` | Section 10.3 lifecycle matrix | unchanged; already contained the selected deterministic result |
| `AI-002_REMOVAL_SEMANTICS.md` | Sections 3, 5–9 and 11 | unchanged |
| Clone Identity Specification | all | unchanged |
| Relationship Reference Correction | all | unchanged |
| Version Compatibility | all | unchanged |
| accepted CA-001 | all | unchanged |
| DF-002 | all | unchanged |

## AICR-O-001 disposition

**Disposition: ACCEPTED**

No normative clarification is required.

- Clone `UNKNOWN` is a result in the clone-classification domain.
- Compatibility `UNKNOWN` is a result in the compatibility-decision domain.
- The identical label does not define a shared enum, schema field, state machine
  or transition model.

Both prohibit inference and invoke their respective fail-closed boundary, but
their domain-specific types remain intentionally separate. This explanation is
non-normative and does not modify either closed result set.

## AICR-O-002 disposition

**Disposition: ACCEPTED**

No normative clarification is required.

- `FAIL_CLOSED` is the Clone Identity activation outcome.
- `CAPABILITY_FAIL_CLOSED` is the Relationship Reference capability-boundary
  outcome.
- Both apply the inherited fail-closed principle, but they are not
  interchangeable normative values.

Removal and version documents consume the common safety consequence at their
own boundaries without importing either value into their state/result sets.
This explanation is non-normative and changes no established vocabulary.

## Before/after semantic comparison

| Dimension | Before | After | Architecture effect |
|---|---|---|---|
| Prior state | `REMOVED` | `REMOVED` | none |
| Event | continued absence in successful collection | identical | none |
| Result state | `REMOVED` in both locations | `REMOVED` in both locations | ambiguity removed |
| Consequence | one conditional phrase had no defined alternative | continued absence retains `REMOVED` | existing matrix made explicit |
| Reappearance/recreation | `ACTIVE` with positive valid evidence | unchanged | none |
| Elapsed time/repeated absence | no automatic new classification | unchanged and explicit | none |
| Historical retention | orthogonal `HISTORICAL` designation | unchanged | none |

## State and compatibility preservation

The five current-source states remain closed and unchanged:

- `ACTIVE`
- `NOT_OBSERVED`
- `UNAVAILABLE`
- `REMOVED`
- `IDENTITY_INVALID`

`HISTORICAL` remains an orthogonal retention designation, not a sixth current
state. Clone classifications/outcomes, relationship results, compatibility
results and CA-001 cryptographic values remain separate closed vocabularies.

## Validation and finding disposition

| Review item | Disposition | Evidence |
|---|---|---|
| AICR-F-001 | `RESOLVED` | Section 4.2 and Section 10.3 now both return unconditional `REMOVED` for prior `REMOVED` plus continued successful absence |
| AICR-O-001 | `ACCEPTED` | domain-specific `UNKNOWN` meanings were already explicit and non-conflicting; no normative edit made |
| AICR-O-002 | `ACCEPTED` | layer-specific fail-closed values were already explicit and behaviorally consistent; no normative edit made |

Validation conclusions:

- Removal prose/table outcomes for the affected transition: identical.
- Undefined result for prior `REMOVED` plus continued absence: none.
- Current-state count or meaning changed: 0.
- Historical-retention meaning changed: 0.
- Clone, relationship, version or CA-001 rule changed: 0.
- New requirement introduced: 0.
- Implementation detail introduced: 0.
- Governance changed: 0.
- Contract changed or activated: 0.

**AICR_F001_RESOLVED**
