# AI-002 Relationship Reference Correction

## 1. Purpose

### 1.1 Normative scope

This document normatively closes AI-002 Correction C-003 / R003-F-003. It
defines exactly one public `source_ref` representation for every Release 1
relationship and defines its validation, lifecycle, privacy, identity and
migration semantics.

The key words `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`,
`SHOULD NOT` and `MAY` are normative.

### 1.2 Inherited authority

- DF-002 remains the implementation baseline. Its frozen relationship model
  requires relationship endpoints to use the same opaque tokens as observations
  and identifies a relationship by `(predicate, source_ref, target_ref)`.
- AI-001 supplies unchanged predicate names, explicit-source requirements,
  target-reference rules, relationship-ID framing and deterministic ordering.
- R003-F-003 establishes that AI-001's use of entity `obs1_...` as `source_ref`
  conflicts with DF-002's same-opaque-token rule.
- Accepted CA-001 supplies the only accepted protected entity-reference
  construction: `refh1_entity_` plus the complete lowercase HMAC-SHA-256 result.
- The AI-002 Clone Identity Specification supplies continuity,
  discontinuity and unknown/fail-closed classification effects.

### 1.3 Out of scope

This correction does not:

- change any Release 1 predicate, target-reference meaning or cardinality;
- redefine CA-001 HMAC, framing, domain, secret, collision or lifecycle rules;
- redesign clone identity or its decision model;
- redefine canonical-key or observation-ID algorithms;
- resolve removal versus `IDENTITY_INVALID` for observations;
- select or activate a contract version;
- define JSON Schema, storage, API, classes or production implementation.

## 2. Problem statement

DF-002 says relationship references use the same opaque tokens as observations.
The entity observation is based on an opaque entity reference. Its relationship
`source_ref` therefore denotes that same entity reference.

AI-001 instead specifies the entity observation's `obs1_...` observation ID as
every relationship `source_ref`, while its entity opaque token is a separate
`ref1_entity_...` value. Those values have different domains, inputs, purposes
and lifecycle. This changes the frozen relationship tuple, prevents direct
same-token joins and leaves “same opaque token” ambiguous.

R003-F-003 classifies the conflict as a MAJOR compatibility defect. Accepted
CA-001 deliberately resolves only protected opaque-reference cryptography. It
states that relationship `source_ref` adoption remains outside CA-001, so it
does not decide whether the new `refh1_entity_...` value or an observation ID is
serialized in a relationship.

This correction removes that ambiguity without adding a predicate or changing
the observation-ID construction.

## 3. Normative model

### 3.1 Sole public representation

There is exactly one normative public `source_ref` representation:

```text
source_ref = validated CA-001 entity public reference
source_ref = "refh1_entity_" || 64lowerhex
```

Grammar:

```text
source-ref = "refh1_entity_" 64lowerhex
64lowerhex = 64("0"-"9" / "a"-"f")
```

The complete string is 77 ASCII octets. It is the CA-001 result for
`reference_kind = "entity"`, the current installation scope, current CA-001
secret generation and the authoritative raw entity identifier.

`source_ref` MUST equal the opaque entity reference carried by the corresponding
`entity_display_reference` observation. It MUST NOT equal, contain or be derived
from the observation's `obs1_...` observation ID.

No `ref1_entity_...`, `obs1_...`, canonical key, raw entity identifier or second
source-reference form is valid in a current corrected relationship snapshot.

### 3.2 Lifecycle

- The producer SHALL derive and validate the CA-001 entity reference before
  creating an entity observation or relationship.
- A relationship SHALL use the already validated observation entity reference;
  it SHALL NOT perform a distinct or differently parameterized derivation.
- Equal CA-001 entity-reference inputs in one preserved identity context yield
  the same `source_ref`.
- A CA-001 or Clone Identity discontinuity yields a different `source_ref` and
  replacement relationship identities.
- A last valid immutable snapshot MAY retain its historical `source_ref` only as
  explicitly stale when current collection fails closed.

### 3.3 Stability and uniqueness

Within one CA-001 identity context, one normalized authoritative raw entity
identifier maps to one `source_ref`. The CA-001 collision registry and
fail-closed rules are authoritative; this document adds no collision algorithm.

`source_ref` is stable across repeated collection, restart, update, reload,
hardware/environment-only change and valid Clone Identity continuity when the
CA-001 kind, scope, secret generation and raw entity identifier are unchanged.

`source_ref` changes when any CA-001 identity input changes, including raw
entity identifier, installation scope, secret generation, reference kind,
format version or another identity-affecting CA-001 byte.

### 3.4 Visibility

`source_ref` is public pseudonymous relationship data. Its public visibility
does not make its raw identifier, secret, protected provenance or raw-to-opaque
mapping public. Consumers MAY compare exact `source_ref` strings within the
declared snapshot/installation context. They MUST NOT reverse, guess, rederive
or treat cross-installation equality as meaningful.

### 3.5 Validation

A `source_ref` is valid only if:

1. its grammar matches Section 3.1 exactly;
2. its kind is exactly lowercase `entity`;
3. its 64 hexadecimal characters are lowercase and untruncated;
4. it was validated under accepted CA-001 for the current identity context;
5. it exactly equals the entity opaque reference in the corresponding valid
   observation;
6. the relationship and observation use the same installation scope, secret
   generation, cryptographic format and immutable snapshot context.

String grammar alone is insufficient to establish validity.

## 4. Relationship semantics

### 4.1 Relationship creation

A relationship SHALL be created only when the authoritative source response
explicitly supplies the predicate/target fact, the source observation is valid,
`source_ref` passes Section 3.5 and `target_ref` passes its frozen validation.
No name, domain, availability, shared attribute or inferred association may
create a relationship.

The canonical relationship tuple remains:

```text
(predicate, source_ref, target_ref)
```

AI-001's relationship-ID algorithm and ordering remain unchanged except that
the corrected `source_ref` bytes are its source input:

```text
relationship_id = "rel1_" || lowercase_hex(SHA-256(
  frame("hadocs-generic-metadata/relationship-id/v1") ||
  frame(installation_scope) ||
  frame(predicate) ||
  frame(source_ref) ||
  frame(target_ref)
))
```

This document does not activate that serialized proposal or choose its future
contract-major treatment; C-005 remains responsible for version disposition.

### 4.2 Persistence

If the explicit source fact and all canonical tuple values remain equal in the
next valid snapshot, the relationship and `relationship_id` SHALL remain equal.
Relationship order has no persistence meaning.

Historical relationships remain facts about their immutable snapshots. Current
absence does not erase or invalidate them.

### 4.3 Replacement

A relationship is replaced, not mutated, when predicate, `source_ref` or
`target_ref` changes. The previous tuple SHALL be absent from the new snapshot
and a new valid tuple/relationship ID SHALL be emitted only if the explicit
source fact exists.

Replacement MUST NOT create an alias between old and new endpoints.

### 4.4 Deletion/current absence

When an explicit relationship fact is absent from a successfully collected
current source snapshot, the previous relationship SHALL be absent from the
current relationship set. Absence MUST NOT assert non-membership, deletion of
the underlying source object, health, failure or historical invalidity.

If collection is partial or failed, absence MUST NOT be synthesized from the
failed capability. Capability status and stale-snapshot rules remain
authoritative.

### 4.5 Recreation

If a relationship fact later reappears:

- equal predicate, equal validated `source_ref` and equal `target_ref` SHALL
  recreate the same canonical tuple and relationship ID;
- any unequal tuple component SHALL create a replacement relationship with a
  different identity;
- raw-source similarity MUST NOT alias unequal public endpoints.

### 4.6 Continuity

Clone result `SAME_LOGICAL_INSTALLATION + PRESERVE_CONTEXT` preserves
`source_ref` when the raw entity identifier and CA-001 format/kind are also
equal. Equal explicit relationship facts therefore preserve their canonical
relationship tuple.

### 4.7 Discontinuity

Clone result `DISTINCT_LOGICAL_INSTALLATION + NEW_CONTEXT_REQUIRED` requires a
new installation scope and CA-001 secret generation. Every entity `source_ref`
and every relationship tuple containing it SHALL be replaced after the new
context is valid. Old and new source references MUST NOT be aliased.

Clone result `UNKNOWN + FAIL_CLOSED`, or known continuity with CA-001 state
unavailable, SHALL publish no new relationship requiring the protected source
reference. A last valid immutable relationship set MAY remain explicitly stale.

## 5. Identity interaction

### 5.1 Installation scope

Installation scope is an authenticated CA-001 input and remains a framed input
to the frozen relationship-ID construction. Same-scope continuity can preserve
`source_ref`; a new scope requires replacement. Cross-installation relationship
tuples are prohibited.

### 5.2 CA-001 references

CA-001 is the sole derivation authority for `source_ref`. This document neither
adds an HMAC domain nor derives a relationship-specific source token. Entity,
device, area and label reference kinds remain cryptographically separated.
Only the `entity` kind is valid as relationship `source_ref` in Release 1.

### 5.3 Observation identity

The entity observation and its relationship share the same opaque entity
reference but retain different identity purposes:

- `source_ref` is `refh1_entity_...`;
- `observation_id` is independently computed by the frozen `obs1_...`
  observation-ID algorithm from installation scope, source capability and
  canonical key;
- the entity canonical key contains the corrected opaque entity reference as
  its category component;
- `source_ref` MUST NOT equal or be derived from `observation_id`.

Changing from legacy/proposed `ref1_entity_...` to accepted
`refh1_entity_...` changes the entity canonical-key component and therefore the
downstream entity observation ID. The observation-ID algorithm, domain, framing
and grammar do not change.

### 5.4 Clone identity

| Clone Identity result | Source-reference result |
|---|---|
| `SAME_LOGICAL_INSTALLATION + PRESERVE_CONTEXT` | Preserve when authoritative raw entity ID and CA-001 format/kind are equal |
| `DISTINCT_LOGICAL_INSTALLATION + NEW_CONTEXT_REQUIRED` | Replace all entity source references under the new context |
| `UNKNOWN + FAIL_CLOSED` | Emit no new protected source reference or dependent relationship |
| `SAME_LOGICAL_INSTALLATION + FAIL_CLOSED` | Preserve intended lineage but emit no new source reference until exact CA-001 recovery |

### 5.5 Transition inventory

Transitions that preserve `source_ref` when the raw entity identifier is equal:

- repeat collection;
- process/application/host restart;
- normal update and configuration reload;
- hardware/environment-only change with uninterrupted valid lineage;
- authoritative restore/migration/replacement classified as
  `SAME_LOGICAL_INSTALLATION + PRESERVE_CONTEXT`;
- temporary collection failure followed by exact recovery of the same context.

Transitions that require replacement:

- authoritative separation or validated fresh installation;
- installation-scope generation change;
- CA-001 secret-generation change;
- CA-001 format/domain/framing/kind change under a future approved format;
- authoritative raw entity-identifier change;
- any transition classified `DISTINCT_LOGICAL_INSTALLATION`.

Unknown or invalid transitions do not preserve or replace current output; they
fail closed pending resolution.

## 6. Privacy

The producer and consumer MUST NOT:

- serialize a raw entity/device/area/label identifier in `source_ref`;
- serialize, log, hash for diagnostics or expose CA-001 secret material;
- export private raw-to-opaque mappings, collision-registry tuples, clone
  declarations or protected provenance;
- provide a reversible public mapping or recovery endpoint;
- use an unkeyed/public-scope-only derivation;
- correlate, alias or join `source_ref` across distinct installation contexts;
- reuse one CA-001 secret across distinct logical installations;
- expose raw identifiers or legacy values as fallback when validation fails;
- treat equal-looking values from unsupported formats as identity-equivalent.

Public predicate and allowed target semantics remain visible as frozen by
DF-002. `source_ref` exposes only its kind and pseudonymous digest.

## 7. Validation

### 7.1 Deterministic validation procedure

Validate in this exact order:

1. Validate current capability/snapshot and Clone Identity activation state.
2. Validate corresponding entity observation and its CA-001 entity reference.
3. Validate `source_ref` grammar and exact equality with that observation
   reference.
4. Validate same scope, secret generation and CA-001 format context.
5. Validate predicate against the frozen four-value vocabulary.
6. Validate `target_ref` under its frozen predicate-specific rule.
7. Validate explicit source fact and resolution semantics.
8. Construct canonical tuple and relationship ID.
9. Reject duplicate-identity inconsistency or unequal tuple collision under the
   frozen relationship collision rule.
10. Sort only after all relationships validate.

The first failure determines the outcome in Section 9. No later step may repair
or reinterpret an earlier failure.

### 7.2 Malformed source_ref

A `source_ref` is malformed if any of these holds:

- wrong prefix, kind, length or separator;
- uppercase or non-hex digest characters;
- truncated, extended or padded digest;
- whitespace, NUL, control character, Unicode lookalike or non-ASCII byte;
- `ref1_`, `obs1_`, canonical-key or raw-ID representation;
- any syntactically alternate/aliased spelling.

A malformed `source_ref` invalidates the relationship. It MUST NOT invalidate
an independently valid observation.

### 7.3 Invalid source_ref

A grammar-correct `source_ref` is invalid if it:

- was not validated under the current CA-001 context;
- differs from the corresponding observation entity reference;
- uses a different scope, secret generation, format or snapshot;
- is associated with missing/invalid protected inputs;
- is implicated in a CA-001 collision or clone ambiguity gate;
- is a current relationship reference from a historical/unsupported format.

Invalid protected source state that prevents safe capability construction fails
closed at the affected capability snapshot boundary under CA-001/Clone Identity.
An isolated serialized relationship with a malformed/mismatched value is
rejected without rewriting the observation.

### 7.4 Prohibited values

Prohibited `source_ref` values include raw IDs, URLs, hostnames, addresses,
unique IDs, device IDs, area IDs, label IDs, account values, canonical keys,
`obs1_...`, `ref1_...`, non-entity `refh1_...`, secret-derived diagnostics and
consumer-supplied tokens.

## 8. Migration

### 8.1 Frozen DF-002 meaning

DF-002's abstract rule remains: relationship source references use the same
opaque entity token as the observation. This correction restores that meaning;
it does not amend the predicate model.

### 8.2 Historical/proposed forms

- AI-001 `source_ref = obs1_...` is rejected and MUST NOT be emitted by the
  corrected model.
- AI-001 `ref1_entity_...` is not byte-compatible with accepted CA-001
  `refh1_entity_...` and MUST NOT be aliased.
- Historical artifacts MAY retain their original bytes and provenance as
  historical evidence.
- One current snapshot SHALL use one source-reference format only. Mixed
  `obs1_`, `ref1_entity_` and `refh1_entity_` source references are invalid.

### 8.3 Future activation boundary

If a later Design Freeze and contract authority activate this correction, the
transition SHALL occur at one immutable snapshot boundary:

- derive/validate all current CA-001 references;
- regenerate affected entity canonical keys and observation IDs using unchanged
  AI-001 algorithms;
- regenerate all relationship tuples/IDs containing corrected source refs;
- retain historical snapshots without aliasing;
- publish no raw mapping between old and new values;
- fail closed rather than publish a mixed snapshot.

This section defines architecture migration semantics only. It does not select
the future contract version, activate migration, define persistence or authorize
implementation.

## 9. Decision tables

### 9.1 Creation/validation table

Rows are evaluated top to bottom. The first match is final.

| Priority | Source observation/reference state | Explicit relationship fact | Target state | Exact outcome |
|---:|---|---|---|---|
| 1 | Clone/CA-001 capability fail-closed | any | any | `CAPABILITY_FAIL_CLOSED`; emit no new relationship set |
| 2 | Missing or invalid source observation | any | any | `RELATIONSHIP_ABSENT`; no source relationship can be created |
| 3 | Malformed/mismatched `source_ref` in candidate relationship | present | any | `RELATIONSHIP_INVALID`; reject candidate, preserve independent valid observation |
| 4 | Valid source | absent in successful source snapshot | any | `RELATIONSHIP_ABSENT`; absence proves no non-membership |
| 5 | Valid source and explicit fact | invalid/malformed target | invalid | `RELATIONSHIP_INVALID`; apply frozen partial/reference rules |
| 6 | Valid source and explicit fact | present | valid or permitted `reference_only` | `RELATIONSHIP_EMIT` with canonical tuple |
| 7 | Any unlisted/contradictory state | any | any | `RELATIONSHIP_INVALID`; no inference/fallback |

### 9.2 Lifecycle table

| Prior valid relationship | Current state | Exact outcome |
|---|---|---|
| none | same explicit valid tuple appears | `CREATE` |
| present | same explicit valid tuple remains | `PRESERVE` |
| present | predicate/source/target changes to another valid tuple | `REPLACE`; old absent, new emitted |
| present | explicit fact absent after successful collection | `CURRENT_ABSENT`; historical tuple remains valid |
| present | collection partial/failed | `NO_NEGATIVE_ASSERTION`; use capability/stale rules |
| absent | identical valid tuple reappears | `RECREATE_SAME_ID` |
| absent/present | clone/CA-001 continuity with equal inputs | preserve/recreate according to explicit fact |
| absent/present | clone/CA-001 discontinuity | `REPLACE_CONTEXT`; regenerate all affected tuples |
| any | clone/CA-001 unknown/failure | `CAPABILITY_FAIL_CLOSED`; no new tuple |
| any | malformed/invalid source ref | `RELATIONSHIP_INVALID`; no repair or alias |

### 9.3 Identity-transition table

| Transition | source_ref | relationship tuple/ID | Outcome |
|---|---|---|---|
| Repeat/restart/update/reload, equal inputs | unchanged | unchanged if explicit fact equal | `PRESERVE` |
| Valid same-lineage restore/migration/replacement | unchanged | unchanged if explicit fact equal | `PRESERVE` |
| Hardware/environment-only change | unchanged | unchanged if explicit fact equal | `PRESERVE` |
| Raw entity identifier changes | replace | replace every affected tuple | `REPLACE` |
| Scope or secret generation changes | replace | replace every affected tuple | `REPLACE_CONTEXT` |
| Distinct logical installation | replace under new context | replace; no cross-context alias | `REPLACE_CONTEXT` |
| Unknown clone classification | no new value | no new relationship | `CAPABILITY_FAIL_CLOSED` |
| Secret/reference/collision failure | no new value | no new relationship | `CAPABILITY_FAIL_CLOSED` |
| Relationship fact removed | source observation may remain | tuple absent currently | `CURRENT_ABSENT` |
| Same fact recreated with same validated tuple | unchanged | same ID | `RECREATE_SAME_ID` |

No relationship state outside Sections 9.1 through 9.3 is valid. Unlisted or
contradictory input resolves to the closed invalid/fail-closed rows, never an
implementation-selected result.

## 10. Traceability

| Rule group | DF-002 | AI-001 | R-003 | Accepted CA-001 | Clone Identity Specification |
|---|---|---|---|---|---|
| Sole `refh1_entity_...` source model | Same opaque token as observation | Entity opaque reference exists but AI-001 incorrectly chose `obs1_` | F-003 requires one frozen-compatible endpoint | Defines accepted entity reference bytes | Continuity context determines preservation |
| Source ref is not observation ID | Separate observation and relationship envelopes | Proposed `obs1_` source is superseded | Identified explicit conflict | Reference purpose differs from observation ID | No clone redesign |
| Same-token observation join | Frozen integrity rule | Entity canonical key contains opaque token | Required compatibility restoration | Accepted token is `refh1_entity_` | Equal context/raw ID preserves |
| Tuple identity and relationship ID | `(predicate, source_ref, target_ref)` | Framing/ordering retained | Tuple bytes affected by correction | Corrected source bytes are stable/collision-checked | Scope continuity/discontinuity supplied |
| Lifecycle create/preserve/replace/absence | Explicit facts only; absence proves nothing | Relationship/dangling/order rules retained | Endpoint ambiguity removed | Fail-closed protected references | Unknown/failure blocks new set |
| Privacy | Raw IDs/mappings excluded; no cross-installation correlation | Raw target/source data excluded | `obs1_` substitution rejected | Keyed non-reversible reference | Distinct contexts replace; unknown blocks |
| Validation | Same opaque token and reference integrity | Malformed ref invalidates relationship only | One exact representation required | Grammar/context/collision authority | Clone activation precedence first |
| Migration | Major identity/privacy change requires governance | Historical `ref1_`/`obs1_` proposals | F-003/F-005 require correction/version treatment | `ref1_` not alias of `refh1_` | Continuity versus discontinuity effects |

### Finding closure

| R-003 finding | Original defect | Corrected rule | Status |
|---|---|---|---|
| R003-F-003 | `source_ref = obs1_...` conflicts with same opaque observation token | `source_ref` is exactly the validated corresponding `refh1_entity_...` entity reference and never the observation ID | `CLOSED` pending combined AI-002 review |

## Validation conclusion

- Normative public `source_ref` representations: exactly 1.
- Representation: `refh1_entity_` plus 64 lowercase hexadecimal characters.
- Lifecycle states with deterministic outcomes: complete.
- Undefined transitions: 0; closed invalid/fail-closed rows apply.
- CA-001 algorithms changed: 0.
- Clone Identity rules changed: 0.
- Implementation/storage/API details introduced: 0.
- Governance changes: 0.
- Contract changes or activation: 0.

**RELATIONSHIP_REFERENCE_CORRECTION_COMPLETE_FOR_AI002_REVIEW_PACKAGE**

