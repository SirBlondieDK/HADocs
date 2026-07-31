# AI-002 Removal Semantics

## 1. Purpose

### 1.1 Normative scope

This document normatively closes AI-002 Correction C-004 / R003-F-004. It
defines the lifecycle meaning of current presence, temporary absence,
unavailability, authoritative removal, invalid identity and historical
retention for observations and relationships.

The key words `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`,
`SHOULD NOT` and `MAY` are normative.

### 1.2 Inherited authority

- DF-002 treats observations as authoritative facts, distinguishes missing from
  unknown/unavailable and prohibits turning absence into a diagnostic or
  negative fact.
- AI-001 category profiles say a removed component/event/entity is absent from
  the current snapshot and can recreate the same deterministic identity when
  the same authoritative identifier reappears.
- R003-F-004 identifies the conflict between those absence rules and AI-001's
  stability matrix, which labeled source removal `IDENTITY_INVALID`.
- Accepted CA-001 defines protected-reference validity, secret/collision
  failure, immutable stale snapshots and historical identity discontinuity.
- The Clone Identity Specification defines continuity, discontinuity and
  `UNKNOWN + FAIL_CLOSED` without defining removal.
- The Relationship Reference Correction defines current relationship absence,
  replacement, recreation and invalid endpoints without defining observation
  removal.

### 1.3 Out of scope

This document does not redefine:

- clone identity, declaration, provenance or transition authority;
- `source_ref`, relationship-ID construction or predicate semantics;
- CA-001 cryptography, secret, collision registry, format or recovery;
- canonical-key or observation-ID construction;
- contract version, schema, persistence implementation or retention duration;
- production code, tests, fixtures, APIs or UI.

## 2. Problem statement

AI-001 contains two incompatible meanings for source removal:

1. category profiles and architecture prose treat removal as absence from the
   current snapshot, without invalidating historical identity; and
2. the stability matrix labels source removal `IDENTITY_INVALID`.

Those meanings produce different consumer, relationship, history and recovery
behavior. A valid object that is no longer present is not the same condition as
a present row whose required identity cannot be normalized or validated.
Likewise, an unavailable source cannot prove either removal or invalidity.

R003-F-004 requires one deterministic partition. This correction reserves
`IDENTITY_INVALID` for exact identity-construction failures and defines removal,
absence, unavailability and history independently.

## 3. Removal model

### 3.1 Entity removal

An entity observation is **currently absent** when its authoritative source row
is not present in a successful, complete collection covering that row's source
scope. Current absence produces `NOT_OBSERVED`, not `IDENTITY_INVALID` and not
an assertion of deletion.

An entity is **REMOVED** only when the authoritative source explicitly reports a
removal/deletion event or state with documented semantics identifying the same
source object. Snapshot absence, elapsed time, missing relationships, unavailable
collection or consumer inference MUST NOT establish `REMOVED`.

If the source interface supplies no authoritative removal signal, the identity
MUST remain `NOT_OBSERVED` regardless of duration; it MUST NOT be promoted to
`REMOVED` by timeout.

### 3.2 Relationship removal

A relationship is currently absent when its explicit source fact is absent from
a successful current source snapshot. This is `CURRENT_ABSENT` under the
Relationship Reference Correction. It does not remove or invalidate either
endpoint and does not prove non-membership.

Authoritative removal of a source observation makes every relationship using
that observation absent from the current relationship set. Historical
relationship tuples remain facts about their historical snapshots.

### 3.3 Identity invalidation

`IDENTITY_INVALID` means that a present or attempted current identity input
cannot be safely normalized, derived or validated under the frozen identity
rules. It is limited to:

- malformed or prohibited authoritative identity input;
- duplicate normalized identities with contradictory source data;
- observation-ID collision under the frozen observation-ID rule;
- CA-001 protected-reference collision or invalid protected input;
- grammar-correct but context-invalid identity/reference;
- internally inconsistent required identity tuple.

`IDENTITY_INVALID` is not removal, offline state, non-observation, deletion,
unsupported capability, permission failure, authentication failure or ordinary
absence.

### 3.4 Logical removal

**Logical removal** means exclusion from the current successful snapshot. It
maps to `NOT_OBSERVED` unless an authoritative removal signal supports
`REMOVED`. Logical removal affects current output only; it does not erase
historical identity.

### 3.5 Historical removal

**Historical removal** means deletion of a complete retained historical
artifact under a separately governed retention policy. It is not a source
lifecycle event and MUST NOT change a current or future deterministic identity.

Historical artifacts MUST NOT be selectively rewritten to remove one endpoint
while retaining a relationship that would misrepresent that immutable snapshot.
Private provenance and collision state required by CA-001 or Clone Identity are
not public historical artifacts and remain governed by their stricter retention
requirements.

### 3.6 Temporary absence

**Temporary absence** is `NOT_OBSERVED` when a successful complete collection
does not contain the object/fact and no authoritative removal signal exists.
The architecture does not infer whether that absence will be brief or permanent.

### 3.7 Permanent removal

**Permanent removal** is represented by `REMOVED` only when authoritative
source semantics explicitly establish removal. “Permanent” is not inferred from
time. Recreation remains possible and follows Section 4.4; historical validity
is unaffected.

## 4. Identity lifecycle

### 4.1 State model

Five mutually exclusive **current-source states** are sufficient and required:

| Current state | Exact meaning | Current observation |
|---|---|---|
| `ACTIVE` | Valid authoritative source input is present and the identity validates | emitted |
| `NOT_OBSERVED` | Latest successful complete collection does not contain the source object/fact; no explicit removal is established | absent |
| `UNAVAILABLE` | Current collection cannot authoritatively determine presence/absence | no new conclusion; last valid snapshot may be stale |
| `REMOVED` | Authoritative source semantics explicitly establish removal of the identified object/fact | absent |
| `IDENTITY_INVALID` | Present/attempted current identity input cannot safely validate under exact identity rules | invalid candidate not emitted; affected boundary reports failure/partial status |

`HISTORICAL` is a separate **retention designation**, not a sixth current-source
state. A previously valid `ACTIVE` observation or relationship becomes
`HISTORICAL` when retained in an immutable non-current snapshot. Separating the
axes avoids claiming that retained history describes current source presence.

### 4.2 Allowed transitions

Every transition is deterministic:

| From | Event/evidence | To | Current-output consequence |
|---|---|---|---|
| no prior identity | valid source and identity | `ACTIVE` | create observation |
| no prior identity | successful complete collection lacks object | `NOT_OBSERVED` | emit nothing |
| no prior identity | collection unavailable/partial for presence | `UNAVAILABLE` | emit nothing; no absence claim |
| no prior identity | malformed/prohibited present identity | `IDENTITY_INVALID` | reject candidate; affected capability partial/fail boundary |
| `ACTIVE` | same valid identity observed | `ACTIVE` | preserve deterministic identity |
| `ACTIVE` | complete successful snapshot lacks object, no removal signal | `NOT_OBSERVED` | omit current observation; retain history |
| `ACTIVE` | authoritative removal signal | `REMOVED` | omit current observation; retain history |
| `ACTIVE` | collection cannot determine presence | `UNAVAILABLE` | no new conclusion; last valid may remain stale |
| `ACTIVE` | present identity becomes malformed/colliding | `IDENTITY_INVALID` | reject current candidate; historical valid identity remains valid |
| `NOT_OBSERVED` | same valid identity reappears | `ACTIVE` | recreate same identity in same identity context |
| `NOT_OBSERVED` | authoritative removal later established | `REMOVED` | remain absent; record authoritative removal state |
| `NOT_OBSERVED` | collection unavailable | `UNAVAILABLE` | no new conclusion |
| `REMOVED` | same valid authoritative identifier reappears | `ACTIVE` | recreate deterministic identity; no physical-object continuity inference |
| `REMOVED` | object remains absent in successful collection | `REMOVED` | remain absent; continued absence alone does not create a new classification |
| `UNAVAILABLE` | successful collection observes valid identity | `ACTIVE` | emit/recover current observation |
| `UNAVAILABLE` | successful complete collection lacks object | `NOT_OBSERVED` | omit; no deletion inference |
| `UNAVAILABLE` | authoritative removal signal | `REMOVED` | omit; retain history |
| `UNAVAILABLE` | unavailability continues | `UNAVAILABLE` | no new conclusion |
| `IDENTITY_INVALID` | corrected present input validates | `ACTIVE` | emit derived identity; alias only if exact deterministic inputs equal a prior valid identity |
| `IDENTITY_INVALID` | input absent in successful complete collection | `NOT_OBSERVED` | omit; invalid attempt is not a historical valid identity |
| `IDENTITY_INVALID` | invalid condition continues | `IDENTITY_INVALID` | reject candidate |
| any state | Clone Identity `UNKNOWN + FAIL_CLOSED` | current state not advanced | no new current identity conclusion; last valid may be stale |
| any state | distinct-installation discontinuity | evaluated independently in new context | old identity remains historical only; no alias/resurrection |

Any event not matching a row resolves through Section 10's closed decision table,
not implementation choice.

### 4.3 Identity history

Only successfully validated identities can become historical identities.
Malformed/invalid candidate bytes MUST NOT become historical identity records.
A transition to `NOT_OBSERVED`, `UNAVAILABLE`, `REMOVED` or
`IDENTITY_INVALID` MUST NOT retroactively invalidate a prior valid observation.

### 4.4 Recreation

Recreation with the same normalized authoritative identity inputs, same
installation scope, same CA-001 secret generation and same frozen identity
formats SHALL reproduce the same public reference, canonical key and
observation ID. This equality establishes identifier equality only; it MUST NOT
assert that the physical/source object instance is the same.

Recreation after distinct-installation discontinuity, scope/secret change, raw
identifier change or identity-format change SHALL produce the identity dictated
by the new context and MUST NOT alias the old identity.

## 5. Temporary absence and source-condition vocabulary

### 5.1 Offline

`offline` is source/system context, not a removal state. If offline status means
the collector cannot complete authoritative collection, the lifecycle result is
`UNAVAILABLE`. Offline MUST NOT produce `NOT_OBSERVED`, `REMOVED` or
`IDENTITY_INVALID` by itself.

### 5.2 Missing

`missing` MUST be interpreted by location:

- an entire source row absent from a successful complete source scope produces
  `NOT_OBSERVED`;
- a required identity field missing from a present row produces
  `IDENTITY_INVALID`;
- required collection data missing because the capability is partial or failed
  produces `UNAVAILABLE`;
- missing protected CA-001/Clone Identity state follows their fail-closed rules
  and is not removal.

The producer MUST record the precise condition and MUST NOT export the ambiguous
word `missing` as the lifecycle conclusion.

### 5.3 Not observed

`not observed` means only `NOT_OBSERVED`: a successful complete source scope did
not contain the object/fact. It is not deletion, failure, health or permanence.

### 5.4 Deleted

`deleted` maps to `REMOVED` only when an authoritative documented source signal
explicitly identifies deletion of that object/fact. User-facing wording,
timeout, snapshot difference or local inference is insufficient.

### 5.5 Removed

`removed` is the normative `REMOVED` state defined in Section 3.7. It requires
authoritative removal evidence and affects current output, not historical
validity.

### 5.6 Unavailable

`unavailable` means `UNAVAILABLE`: current presence cannot be authoritatively
determined. It MUST NOT be treated as object absence, removal, invalid identity,
offline proof or error cause.

## 6. Historical retention

### 6.1 Data that SHALL remain

While the relevant identity context remains usable, the following SHALL remain
according to their inherited private integrity requirements:

- CA-001 collision-registry entries covering accepted/attempted tuples;
- Clone Identity protected lineage and generation/discontinuity provenance;
- immutable references needed to prove which scope, secret generation, format
  and snapshot produced retained history;
- historical validity status distinguishing valid identity from invalid attempt.

An `ACTIVE` identity that becomes non-current SHALL retain its deterministic
identity semantics in any retained immutable historical snapshot.

### 6.2 Data that MAY remain

Subject to a separately governed retention policy:

- complete immutable public historical snapshots;
- their observations, public references and relationship tuples;
- a last valid immutable snapshot explicitly marked stale during
  `UNAVAILABLE`/fail-closed collection;
- non-secret audit metadata allowed by the frozen privacy model.

Retention MAY end for complete historical artifacts, but deletion MUST NOT be
interpreted as source removal or permission to reuse/alias identity.

### 6.3 Data that MUST disappear from current output

The following MUST NOT appear as current facts:

- observation in `NOT_OBSERVED` or `REMOVED`;
- relationship whose explicit current fact is absent;
- invalid/malformed candidate observation or relationship;
- identity-dependent current data blocked by `UNAVAILABLE`, clone ambiguity,
  secret failure or collision failure;
- old-context identity presented as current after discontinuity.

### 6.4 Data that MUST never be retained publicly

Raw source identifiers, secret bytes/digests, raw-to-opaque mappings, private
collision tuples, protected clone declarations/provenance and reversible
cross-generation mappings MUST NOT be exported as public history.

### 6.5 Historical references and relationships

Historical public references and relationship tuples MAY remain only inside
their immutable snapshot/context provenance. They MUST NOT be rewritten to new
references, joined across distinct installations, resurrected into current
output without current authoritative evidence or aliased across discontinuity.

## 7. Clone interaction

This section consumes the Clone Identity Specification and does not redefine it.

| Clone classification/outcome | Removal/lifecycle consequence |
|---|---|
| `SAME_LOGICAL_INSTALLATION + PRESERVE_CONTEXT` | Preserve lifecycle/history. Current collection alone determines `ACTIVE`, `NOT_OBSERVED`, `REMOVED`, `UNAVAILABLE` or `IDENTITY_INVALID`. Migration/restore itself is not removal. |
| `DISTINCT_LOGICAL_INSTALLATION + NEW_CONTEXT_REQUIRED` | Evaluate the new installation independently. Old-context observations/relationships are historical only and MUST NOT be resurrected/aliased into the new context. |
| `UNKNOWN + FAIL_CLOSED` | Do not advance current lifecycle or infer removal/absence. A last valid immutable snapshot MAY remain stale. |
| `SAME_LOGICAL_INSTALLATION + FAIL_CLOSED` | Preserve intended lineage but publish no new current identity-dependent state until exact recovery. Do not infer removal. |

Clone separation MUST NOT mark old identities `IDENTITY_INVALID`; it creates an
identity discontinuity. Clone continuity MUST NOT make a currently absent source
`ACTIVE` without current authoritative observation.

## 8. Relationship interaction

This section consumes the Relationship Reference Correction and does not
redefine `source_ref`.

### 8.1 Source observation state

| Source observation state | Current relationship consequence |
|---|---|
| `ACTIVE` | Emit only explicit valid relationship facts |
| `NOT_OBSERVED` | Source relationships are `CURRENT_ABSENT`; no non-membership inference |
| `REMOVED` | Source relationships are `CURRENT_ABSENT`; historical tuples remain valid |
| `UNAVAILABLE` | Publish no negative relationship conclusion; use partial/stale capability behavior |
| `IDENTITY_INVALID` | Emit no relationship requiring the invalid source; independently valid historical tuples remain historical |

### 8.2 Relationship deletion

Relationship deletion/current absence occurs when the explicit relationship
fact is absent from a successful current source snapshot. It MUST NOT set either
endpoint to `REMOVED` or `IDENTITY_INVALID`.

### 8.3 Relationship invalidation

A relationship is invalid only for malformed/invalid endpoint, predicate,
resolution, tuple or collision conditions defined by the Relationship Reference
Correction. It is not invalid merely because it is absent or historical.

### 8.4 Relationship recreation

If the same valid predicate, `source_ref` and `target_ref` reappear in the same
identity context, recreation SHALL reproduce the same tuple and relationship ID.
Different context or endpoint requires replacement; no alias is permitted.

### 8.5 Relationship history

Retained historical relationship tuples remain scoped to their immutable
snapshot. Current deletion/absence does not rewrite history, and history does
not make a relationship current without a current explicit fact.

## 9. Privacy

Removal, invalidation, retention and recreation MUST NOT:

- reveal or retain raw identifiers in public output/history;
- reveal, log or diagnose with CA-001 secret material or secret digests;
- export private collision or clone provenance;
- offer a reversible public mapping between historical/current references;
- correlate or resurrect identity across distinct logical installations;
- alias old/new scope, secret generation, format or raw identifier contexts;
- infer physical-object continuity from deterministic identifier equality;
- use historical relationship/reference equality to bypass current validation;
- expose deletion/absence terminology that overstates authoritative evidence.

Historical artifacts MUST preserve their original public bytes and provenance;
they MUST NOT be re-identified under current keys or contexts.

## 10. Deterministic decision tables

### 10.1 Current observation decision table

Rows are evaluated top to bottom. First match is final.

| Priority | Collection/source condition | Identity condition | Exact state/outcome |
|---:|---|---|---|
| 1 | Clone Identity or CA-001 fail-closed | any | lifecycle not advanced; no new current observation; last valid MAY be stale |
| 2 | Capability cannot authoritatively determine presence | any | `UNAVAILABLE` |
| 3 | Explicit authoritative removal signal | prior/current identity can be identified | `REMOVED` |
| 4 | Present authoritative row | malformed/prohibited/colliding/invalid | `IDENTITY_INVALID` |
| 5 | Present authoritative row | valid | `ACTIVE` |
| 6 | Successful complete source scope lacks row; no removal signal | no current row | `NOT_OBSERVED` |
| 7 | Any contradictory/unlisted state | indeterminate | `UNAVAILABLE`; no inference |

### 10.2 Terminology decision table

| Input term/evidence | Required interpretation | Prohibited interpretation |
|---|---|---|
| offline/inaccessible capability | `UNAVAILABLE` | removed/invalid/not observed |
| row absent in complete successful scope | `NOT_OBSERVED` | deleted/permanent/invalid |
| required identity field missing in present row | `IDENTITY_INVALID` | removed |
| authoritative explicit deletion/removal signal | `REMOVED` | identity invalid |
| relationship fact absent | relationship `CURRENT_ABSENT` | endpoint removed/invalid |
| malformed/colliding identity input | `IDENTITY_INVALID` | removal |
| elapsed absence | retain `NOT_OBSERVED` | automatic permanent removal |
| historical snapshot retained | `HISTORICAL` designation | current active fact |

### 10.3 Lifecycle matrix

| Prior state | Valid present | Complete absent | Explicit removal | Unavailable | Invalid present |
|---|---|---|---|---|---|
| none | `ACTIVE` | `NOT_OBSERVED` | `REMOVED` only with identifiable authoritative target | `UNAVAILABLE` | `IDENTITY_INVALID` |
| `ACTIVE` | `ACTIVE` | `NOT_OBSERVED` | `REMOVED` | `UNAVAILABLE` | `IDENTITY_INVALID` |
| `NOT_OBSERVED` | `ACTIVE` | `NOT_OBSERVED` | `REMOVED` | `UNAVAILABLE` | `IDENTITY_INVALID` |
| `REMOVED` | `ACTIVE` recreation | `REMOVED` | `REMOVED` | `UNAVAILABLE` | `IDENTITY_INVALID` |
| `UNAVAILABLE` | `ACTIVE` | `NOT_OBSERVED` | `REMOVED` | `UNAVAILABLE` | `IDENTITY_INVALID` |
| `IDENTITY_INVALID` | `ACTIVE` after validation | `NOT_OBSERVED` | `REMOVED` only with identifiable authoritative target | `UNAVAILABLE` | `IDENTITY_INVALID` |

### 10.4 Relationship lifecycle matrix

| Source/fact condition | Relationship outcome | Historical outcome |
|---|---|---|
| Source `ACTIVE`, explicit valid tuple | `CREATE` or `PRESERVE` | prior immutable tuple retained per policy |
| Source `ACTIVE`, explicit tuple changed | `REPLACE` | old tuple historical only |
| Source `ACTIVE`, fact absent after success | `CURRENT_ABSENT` | prior tuple remains historical |
| Source `NOT_OBSERVED` or `REMOVED` | `CURRENT_ABSENT` | prior tuple remains historical |
| Source `UNAVAILABLE` | no negative assertion/new tuple | last valid snapshot MAY remain stale |
| Source `IDENTITY_INVALID` | relationship invalid/absent currently | prior valid tuple remains historical |
| Same tuple recreated | `RECREATE_SAME_ID` | no physical-continuity inference |
| Clone/context discontinuity | `REPLACE_CONTEXT` | old tuple not aliased |

### 10.5 Historical retention matrix

| Data class | Current output | Public historical retention | Private required retention |
|---|---|---|---|
| Valid current observation | emit if `ACTIVE` | MAY retain immutable snapshot | provenance as required |
| `NOT_OBSERVED`/`REMOVED` observation | MUST disappear current | prior valid snapshot MAY remain | identity/provenance requirements remain |
| Invalid candidate | MUST NOT emit | MUST NOT become valid historical identity | failure/provenance MAY retain safe status only |
| Valid relationship now absent | MUST disappear current | prior tuple MAY remain immutable | provenance as required |
| Raw ID/secret/private mapping | MUST NOT emit | MUST NOT retain publicly | only inherited private state rules apply |
| Collision/clone provenance | MUST NOT emit | MUST NOT retain publicly | SHALL remain per CA-001/Clone Identity |

No lifecycle event outside these tables is undefined. Contradictory/unlisted
current evidence resolves to `UNAVAILABLE` and no negative inference; unsafe
identity evidence resolves to `IDENTITY_INVALID` only when the present identity
input itself fails validation.

## 11. Traceability

| Rule group | DF-002 | AI-001 | R-003 | Accepted CA-001 | Clone Identity Specification | Relationship Reference Correction |
|---|---|---|---|---|---|---|
| Removal is not invalid identity | Missing/unknown not errors; facts only | Profiles use current absence | F-004 identifies conflict | Protected failure separate from absence | Unknown does not infer removal | Relationship absence not endpoint invalidity |
| `NOT_OBSERVED` | No inference from absence | Component/event/entity removal absent current | Required unambiguous removal result | No cryptographic impact | Same/new context independent | `CURRENT_ABSENT` relation behavior |
| `REMOVED` requires explicit evidence | Authoritative fields only | No reliable permanence inference | Prevent semantic overreach | Historical refs remain valid | Classification separate | Current relationship set only |
| `IDENTITY_INVALID` closed scope | Validation/collision errors distinct | Invalid row behavior | Matrix misuse corrected | Collision/invalid protected input | Invalid provenance fail-closed | Malformed/mismatched endpoint invalid |
| `UNAVAILABLE` | Capability statuses/partial/stale | Missing source produces no observation | Distinguish from removal | Last valid stale allowed | UNKNOWN/failure blocks advance | No negative relationship assertion |
| Historical validity | Immutable snapshots/provenance | Recreation deterministic | Removal must not invalidate history | Old snapshots retain bytes | Discontinuity no alias | Historical tuples immutable |
| Recreation | Deterministic identities | Same identifier reuses identity | F-004 closure expectation | Same context reproduces refs | Context determines preserve/change | Same tuple recreates same ID |
| Privacy/no resurrection | No raw mappings/correlation | Prohibited sensitive fields | Avoid unsafe lifecycle inference | Secret/raw mapping private | Distinct contexts separated | No source-ref alias |

### Finding closure

| R-003 finding | Original defect | Corrected rule | Status |
|---|---|---|---|
| R003-F-004 | Source removal was both absence and `IDENTITY_INVALID` | Successful complete non-observation is `NOT_OBSERVED`; explicit authoritative deletion is `REMOVED`; only present/attempted identity-validation failure is `IDENTITY_INVALID`; unavailability remains separate | `CLOSED` pending combined AI-002 review |

## Validation conclusion

- Current-source lifecycle states: 5, mutually exclusive.
- Historical retention designation: 1, orthogonal to current state.
- Temporary absence, unavailability, removal and invalidity: deterministically
  separated.
- Undefined transitions: 0; closed tables apply.
- Historical observation/reference/relationship behavior: defined.
- Clone Identity rules changed: 0.
- Relationship `source_ref` rules changed: 0.
- CA-001 cryptography changed: 0.
- Observation-ID/canonical-key algorithms changed: 0.
- Implementation/storage/API details introduced: 0.
- Governance changes: 0.
- Contract changes or activation: 0.

**REMOVAL_SEMANTICS_COMPLETE_FOR_AI002_REVIEW_PACKAGE**
