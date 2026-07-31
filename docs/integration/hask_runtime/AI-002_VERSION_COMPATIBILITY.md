# AI-002 Version Compatibility

## 1. Purpose

### 1.1 Normative scope

This document normatively closes AI-002 Correction C-005 / R003-F-005. It
defines the compatibility vocabulary, version dimensions, deterministic
compatibility decisions, failure boundary, coexistence expectations and future
evolution rules for the observation-identity correction.

The key words `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`,
`SHOULD NOT` and `MAY` are normative.

### 1.2 Inherited authority

- DF-002 remains the active implementation baseline. Its active Collector
  Contract is `hadocs-generic-metadata 1.0.0`, with four capabilities, four
  observation categories and four relationship predicates.
- The frozen Version Strategy makes the public contract version independent of
  Home Assistant and producer implementation versions. It permits additive,
  semantics-preserving evolution within a major version and requires a major
  boundary for removal or reinterpretation of public semantics.
- AI-001 supplies the unchanged canonical-key, source-capability and
  observation-ID base proposal.
- R003-F-005 requires `INCREMENT_MAJOR_VERSION`: corrected identity and privacy
  semantics cannot remain in contract major version 1.
- Accepted CA-001 fixes cryptographic reference format version `1`, prefix
  family `refh1_`, and identity-affecting byte-change rules independently of the
  public contract version.
- The Clone Identity Specification fixes identity-context continuity and
  discontinuity.
- The Relationship Reference Correction fixes one `source_ref` representation
  and establishes that AI-001 `ref1_`/`obs1_` proposals are not aliases for
  accepted `refh1_` references.
- Removal Semantics fixes current and historical lifecycle meanings without
  changing identity bytes.

### 1.3 Out of scope

This document does not:

- activate, publish or modify a Collector Contract;
- supersede DF-002 or create DF-003;
- define schemas, package names, implementation classes, transport negotiation,
  storage, UI, tests, fixtures or runtime code;
- change CA-001 cryptography, reference framing, prefixes or format version;
- change clone, relationship, removal, canonical-key, observation-ID or
  source-capability semantics;
- authorize migration, implementation, verification or consumer adoption.

The exact successor contract version is **proposed** as
`hadocs-generic-metadata 2.0.0`. It is not active. Only a later independently
reviewed Design Freeze may adopt or replace that proposal.

## 2. Compatibility model

### 2.1 Backward compatibility

Version `N` is **backward compatible** with earlier version `E` only when a
consumer conforming to `E` can process every output permitted by `N` without
misreading a field, identity, relationship, lifecycle state or privacy
guarantee. Ignoring an unknown optional element counts only when the `E`
contract explicitly permits that behavior and the element does not alter the
meaning of known data.

Backward compatibility MUST NOT be claimed across contract major versions by
default. It requires an explicit normative compatibility rule covering the
exact producer and consumer versions.

### 2.2 Forward compatibility

Version `E` is **forward compatible** with later version `N` only when its
contract explicitly requires consumers to ignore the particular unknown
optional extension and all known semantics remain unchanged. Forward
compatibility does not permit a consumer to infer the meaning of an unknown
field, category, identity format, relationship reference or lifecycle value.

Unknown required elements, changed meanings, removed guarantees and unknown
identity-bearing values are not forward compatible.

### 2.3 Unsupported compatibility

Compatibility is **unsupported** when the compared contract-major pair is not
declared supported, when a required feature/version is outside a participant's
declared support set, or when the public artifact violates the selected
contract. Unsupported input SHALL produce `INCOMPATIBLE`; it is not a degraded
form of compatibility.

### 2.4 Unknown compatibility

Compatibility is **unknown** only when required compatibility evidence is
missing or cannot be validated—for example, absent version metadata, malformed
version syntax, an unrecognized version dimension, or missing normative support
declaration. `UNKNOWN` MUST NOT be promoted to compatible or conditionally
compatible by inference, observed success, implementation version, document
date or the absence of a known conflict.

At an identity-bearing public boundary, `UNKNOWN` is fail-closed: the affected
artifact MUST NOT be interpreted, joined, migrated or emitted as current
compatible output.

## 3. Version model

### 3.1 Architecture version

An **architecture version** identifies a normative architecture format or rule
set. CA-001 cryptographic reference format version `1` is an architecture
version. Canonical-key, observation-ID and relationship-ID internal format
markers are likewise architecture dimensions where their defining documents
say so.

Architecture versions:

- govern exact semantics or bytes within their own domain;
- MUST NOT be substituted for the Collector Contract version;
- MAY remain unchanged when a contract major changes, if their bytes and
  meanings remain unchanged;
- MUST change when their own governing architecture declares a change
  identity-affecting.

### 3.2 Contract version

The **contract version** is the SemVer version of the public producer-consumer
contract. It governs public fields, required meanings, compatibility and
consumer obligations.

DF-002 keeps `hadocs-generic-metadata 1.0.0` active. The combined AI-001 plus
AI-002 corrected proposal requires a new major and therefore proposes
`hadocs-generic-metadata 2.0.0`. No `2.x` version becomes active through this
document.

Within a contract major:

- PATCH MUST be editorial or defect correction with identical public semantics
  and accepted values;
- MINOR MAY add optional, independently ignorable elements without changing
  existing meaning;
- MAJOR is REQUIRED for removed, reinterpreted or identity/privacy-affecting
  public semantics.

### 3.3 Implementation version

An **implementation version** identifies producer or consumer software. It MAY
declare which contract and architecture versions it supports, but it MUST NOT
determine compatibility by numeric comparison with them. Two implementation
versions are compatible only through their declared contract support and the
rules in this document.

### 3.4 Document version

A **document version** identifies an editorial revision of a specification or
report. It MUST NOT alter normative semantics without the corresponding
architecture and contract governance. Document revision equality is neither
necessary nor sufficient for runtime compatibility.

### 3.5 Independence and relationships

The four dimensions are independent. Their only normative relationship is:

1. the contract selects the public semantic set;
2. that semantic set references exact architecture formats;
3. an implementation declares support for that contract/architecture set; and
4. documents record those rules without replacing their version authorities.

Home Assistant Core/source API versions remain a separate capability
applicability dimension and MUST NOT substitute for any of these four versions.

## 4. Compatibility decisions

Every comparison SHALL return exactly one of these closed results:

### `COMPATIBLE`

Return `COMPATIBLE` only when:

1. both contract versions are valid and their major versions are equal;
2. the consumer declares support for that major and the producer version falls
   within its declared supported range;
3. every required architecture format is recognized exactly;
4. all required fields and semantics validate;
5. every unknown element is optional and explicitly ignorable; and
6. no identity, privacy, relationship or lifecycle meaning is changed.

### `CONDITIONALLY_COMPATIBLE`

Return `CONDITIONALLY_COMPATIBLE` only when all mandatory semantics validate,
the contract major is supported, and a documented optional capability or
optional element cannot be used but can be omitted without changing remaining
meaning. The decision MUST identify the exact omitted optional surface.

`CONDITIONALLY_COMPATIBLE` MUST NOT be used for an unknown identity format,
unknown required field, major-version mismatch, privacy downgrade, changed
relationship reference or changed lifecycle meaning.

### `INCOMPATIBLE`

Return `INCOMPATIBLE` when any of the following is established:

- contract majors differ and no explicit cross-major compatibility profile
  exists;
- either participant declares the contract/version unsupported;
- a required architecture format is unknown or differs;
- a required field is absent, prohibited or invalid;
- a known field, identity, relationship, lifecycle or privacy guarantee has
  changed meaning;
- an identity-affecting byte/domain/version/secret/context change is presented
  as the old identity format;
- a current snapshot mixes reference formats or contract-major semantics; or
- validation detects a prohibited alias, fallback or silent conversion.

### `UNKNOWN`

Return `UNKNOWN` only when the evidence required to choose another result is
unavailable, malformed, unverifiable or contradictory. Unknown is a result, not
a wildcard. It has the fail-closed behavior defined in Section 5.

## 5. Runtime behavior

This section specifies public-boundary behavior, not an implementation design.

### 5.1 Compatible input

For `COMPATIBLE`, the participant MAY consume or emit the validated surface
covered by the declared contract and architecture support.

For `CONDITIONALLY_COMPATIBLE`, it MAY consume or emit only the validated
mandatory surface and the supported optional surface. It MUST record the exact
optional omission and MUST NOT synthesize replacement meaning.

### 5.2 Incompatible input

On `INCOMPATIBLE`, a participant MUST:

- reject activation/interpretation of the affected public artifact or snapshot;
- emit no current identity, relationship or lifecycle conclusion from it;
- preserve an already valid immutable historical artifact under its original
  version/context when retention is authorized;
- report the incompatibility without exposing raw identifiers or secret
  material; and
- require an explicitly supported contract or governed migration before use.

It MUST NOT:

- coerce, relabel, alias or reinterpret the artifact;
- retry it under a different major, architecture format, prefix or secret;
- merge major-1 and proposed major-2 current identity surfaces;
- downgrade privacy or validation;
- treat implementation-version proximity as compatibility; or
- silently fall back to `hadocs-generic-metadata 1.0.0` semantics.

### 5.3 Unknown input

On `UNKNOWN`, a participant MUST fail closed at the affected boundary exactly
as for incompatible current use, but MUST report `UNKNOWN`, not
`INCOMPATIBLE`. It MUST NOT infer incompatibility when evidence is merely
missing, and MUST NOT infer compatibility from successful parsing.

## 6. Migration compatibility

This section defines expectations only; it does not define or activate a
migration implementation.

- Major-1 AI-001 proposed `ref1_`/`obs1_` identity surfaces and the corrected
  `refh1_` relationship model are not aliases and are not byte-compatible.
- A governed transition to the proposed contract `2.0.0` SHALL create a new
  current contract-major boundary. It MUST NOT rewrite a major-1 artifact in
  place or claim identity equality across the boundary.
- Historical major-1 and proposed major-2 artifacts MAY coexist only as
  separately versioned immutable histories with their original contract,
  architecture, installation context and provenance.
- One current snapshot SHALL use exactly one contract major and one complete
  compatible identity/reference set.
- Cross-major joins, relationship resolution and deduplication are prohibited
  unless a future major contract explicitly supplies a reviewed normative
  mapping. No such mapping exists here.
- Clone continuity does not override a contract-major boundary. Clone
  discontinuity does not itself select a contract version.
- Removal/historical retention preserves original bytes and version metadata;
  it does not upgrade an old identity.
- Migration failure or unknown compatibility SHALL preserve the last valid
  immutable history where permitted and publish no migrated current identity.

## 7. Future evolution

Future architecture evolution SHALL:

1. identify every affected version dimension independently;
2. classify every public byte and semantic impact before implementation;
3. preserve identity bytes within an architecture format version;
4. preserve public meaning within a contract major;
5. use a new architecture format/version/prefix for identity-affecting format
   changes where the governing architecture requires it;
6. use a new contract major for removed, reinterpreted, identity-affecting or
   privacy-affecting public semantics;
7. use a minor only for optional, explicitly ignorable, semantics-preserving
   additions;
8. use a patch only when accepted values and public meaning are unchanged;
9. define coexistence and migration normatively before activation; and
10. undergo architecture authority, independent review and Design Freeze before
    implementation.

An undocumented observed behavior, permissive parser or existing
implementation MUST NOT establish compatibility precedent.

## 8. Deterministic decision tables

Rows in each table are evaluated top to bottom; the first matching row is
final.

### 8.1 Contract decision table

| Priority | Evidence | Exact result |
|---:|---|---|
| 1 | Version/support evidence missing, malformed, contradictory or unverifiable | `UNKNOWN` |
| 2 | Contract majors differ and no explicit reviewed cross-major profile exists | `INCOMPATIBLE` |
| 3 | Major/version explicitly unsupported | `INCOMPATIBLE` |
| 4 | Required architecture format/field/semantic invalid, absent or unknown | `INCOMPATIBLE` |
| 5 | Known meaning, identity, relationship, lifecycle or privacy guarantee changed | `INCOMPATIBLE` |
| 6 | Same supported major; mandatory surface valid; unsupported surface is documented optional and independently omittable | `CONDITIONALLY_COMPATIBLE` |
| 7 | Same supported major; required surface valid; unknowns are explicitly ignorable optional additions | `COMPATIBLE` |
| 8 | Same exact supported contract/architecture set; all validation passes | `COMPATIBLE` |
| 9 | Any state not resolved above | `UNKNOWN` |

### 8.2 Version-dimension table

| Changed dimension | No normative impact | Additive optional impact | Identity/semantic/privacy impact | Required consequence |
|---|---|---|---|---|
| Architecture format | same version MAY remain | only if governing architecture permits | new architecture format/version REQUIRED | contract consequence assessed separately |
| Contract | PATCH candidate | MINOR candidate | MAJOR REQUIRED | independent review and Design Freeze before activation |
| Implementation | compatibility unchanged if declared support unchanged | support declaration MAY expand | cannot redefine contract | decide through contract/architecture support, never implementation number |
| Document | editorial revision | may document an already approved optional addition | cannot introduce normative change alone | corresponding architecture/contract governance REQUIRED |

### 8.3 Current baseline and proposal table

| Compared surface | Result | Required treatment |
|---|---|---|
| DF-002 active `1.0.0` against itself | `COMPATIBLE` only for exact frozen major-1 semantics | remains active baseline; no AI-002 correction activated |
| DF-002 `1.0.0` versus proposed corrected `2.0.0` | `INCOMPATIBLE` | separate current snapshots; no alias, fallback or mixed identity surface |
| Proposed `2.0.0` consumer with exact proposed `2.0.0` producer | potentially `COMPATIBLE` after future freeze, implementation declaration and validation | this document does not activate or verify it |
| Any proposed `2.x` artifact before Design Freeze/activation | `UNKNOWN` for operational use | fail closed; architecture proposal only |
| Historical major 1 plus historical major 2 | not a current compatibility join | MAY coexist only as separately versioned immutable histories |

### 8.4 Evolution decision table

| Change | Contract consequence |
|---|---|
| Editorial text only; accepted values and semantics identical | PATCH MAY be proposed |
| Optional independently ignorable field/capability; existing semantics identical | MINOR MAY be proposed |
| Required field added or removed | MAJOR REQUIRED |
| Existing field/identity/relationship/lifecycle meaning changed | MAJOR REQUIRED |
| Privacy guarantee weakened or identity disclosure changed | MAJOR REQUIRED; separate privacy review |
| CA-001 normative byte, domain, version, secret context or prefix changed | new cryptographic format as required by CA-001; MAJOR contract assessment REQUIRED |
| Unknown impact | no version selected; `UNKNOWN`, fail closed, architecture review REQUIRED |

No table outcome authorizes activation.

## 9. Traceability

| Rule group | DF-002 | AI-001 | R-003 | Accepted CA-001 | Clone Identity | Relationship Reference | Removal Semantics |
|---|---|---|---|---|---|---|---|
| Independent version dimensions | Frozen producer/version strategy | Proposed retaining 1.0.0 | F-005 rejects retention | Cryptographic format v1 independent | Context generation independent | Reference representation independent | Lifecycle state independent |
| Proposed contract `2.0.0` | Active 1.0.0 remains unchanged | Identity semantics were proposed under 1.0.0 | `INCREMENT_MAJOR_VERSION` REQUIRED | New secret/reference privacy semantics | Clone authority/continuity completed | `refh1_` replaces conflicting proposals | Removal meanings corrected |
| Cross-major incompatibility | Major changes break semantics | Proposed identity bytes are public | Major boundary required | `ref1_` not alias of `refh1_` | No cross-context alias | No second public `source_ref` | History retains original bytes |
| Unknown fail-closed | Missing/unsupported is not success | Invalid identity cannot emit | Ambiguity cannot reach implementation | Exact validation/fail-closed | `UNKNOWN + FAIL_CLOSED` | Invalid/dangling refs rejected | Unknown/unavailable does not infer state |
| Conditional compatibility | Additive optional elements tolerated | Closed identity vocabularies unchanged | Major defect cannot be conditional | Identity format cannot be optional fallback | Classification not inferred | Endpoint model mandatory | Lifecycle meanings mandatory |
| Historical coexistence | Immutable snapshots/provenance | Stable identity within context | Migration treatment required | Historical formats may remain evidence | Distinct contexts not aliased | Historical tuples immutable | Historical is separate retention axis |
| Future evolution | Frozen Version Strategy | Identity changes have version consequence | Review precedes DF-003 | Byte change is identity-affecting | Context changes explicit | Reference changes explicit | State meaning changes explicit |

### Finding closure

| R-003 finding | Original defect | Corrected rule | Status |
|---|---|---|---|
| R003-F-005 | AI-001 proposed retaining contract `1.0.0` despite identity/privacy changes governed as major | Preserve active `1.0.0`; propose corrected successor `2.0.0`; treat major-1 and proposed major-2 current surfaces as incompatible; keep internal architecture versions independent | `CLOSED` pending combined AI-002 review |

## Validation conclusion

- Compatibility results: 4, closed and mutually exclusive.
- Undefined compatibility outcomes: 0; final `UNKNOWN` row is fail-closed.
- Version dimensions: 4, independent and explicitly related.
- Proposed successor contract version: `hadocs-generic-metadata 2.0.0`.
- Active contract version changed or activated: 0.
- DF-003 created or implied active: 0.
- CA-001 cryptography/reference format changes: 0.
- Clone, relationship or removal semantics changed: 0.
- Implementation/runtime/schema/package decisions introduced: 0.
- Governance changes: 0.

**VERSION_COMPATIBILITY_COMPLETE_FOR_AI002_REVIEW_PACKAGE**
