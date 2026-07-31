# AI-001 Observation Identity Architecture Proposal

## 1. Status and authority

This document is a governance proposal produced under AI-001. It does not amend DF-002, approve a contract, or authorize implementation. R-003 review and DF-003 are mandatory before implementation resumes.

## 2. Scope

The proposal resolves only the identity blocker recorded by I-001B_RESUME for the four frozen Release 1 observation categories. Release 1 remains four capabilities, four observation categories, four relationship predicates, and zero replacement capabilities or observations.

## 3. Design principles

Identity is deterministic, installation-local, category-aware, source-aware, privacy-reviewed, independent of traversal order and display metadata, and expressed without diagnostic or health semantics.

## 4. Normative framing

For string `s`, `frame(s)` is the four-byte unsigned big-endian length of `NFC(s).encode("utf-8")`, followed by those bytes. Concatenated framed values are unambiguous. All hashes are SHA-256 and render as lowercase hexadecimal.

## 5. Installation scope

The collector owns a persistent raw RFC 4122 UUIDv4 generated with a cryptographically secure random source. It is stored locally, written atomically, included in backup and migration, and never exported. The public scope is:

`is1_` + `hex(SHA-256(frame("hadocs-generic-metadata/installation-scope/v1") || frame(raw_uuid)))`

Missing or corrupt scope prevents creation of a new snapshot and preserves the last valid snapshot as stale. It must not be silently regenerated. A clean installation or intentionally distinct logical clone receives a new scope.

## 6. Source capability vocabulary

The Release 1 vocabulary is closed:

| Observation category | Source capability |
|---|---|
| `api_availability` | `rest.api_root` |
| `loaded_component` | `rest.components` |
| `registered_event_type` | `rest.events` |
| `entity_display_reference` | `websocket.entity_registry.list_for_display` |

Unknown source capabilities are invalid, not dynamically accepted.

## 7. Canonical key

The grammar is `ck1:<category>:<component>`. Components are NFC-normalized and UTF-8 percent-encoded, preserving only ASCII unreserved bytes and using uppercase `%HH`. Case and leading/trailing characters are preserved; no semantic normalization is performed.

## 8. Observation identity

The public observation identifier is:

`obs1_` + `hex(SHA-256(frame("hadocs-generic-metadata/observation-id/v1") || frame(installation_scope) || frame(source_capability) || frame(canonical_key)))`

It is exactly 69 ASCII characters. Any invalid input makes the observation identity invalid; fallback identities are prohibited.

## 9. Category profiles

- `api_availability`: fixed key component `rest_api_root`; one identity per installation.
- `loaded_component`: exact documented component identifier; one identity per distinct component.
- `registered_event_type`: exact documented event type; one identity per distinct event type.
- `entity_display_reference`: canonical component is an installation-scoped `ref1_entity_` token derived from the explicit entity identifier.

The complete rules and vectors are in `AI-001_CATEGORY_IDENTITY_PROFILES.md`.

## 10. Source references

Opaque references use `ref1_<kind>_<digest>` where `kind` is one of `entity`, `device`, `area`, or `label`. The digest covers a domain separator, public installation scope, kind, and NFC raw identifier using normative framing. Raw identifiers are never exported through these references.

## 11. Relationships

Relationships use only the four DF-002 predicates. The source reference is the entity observation ID. A platform target is the deterministically computed `loaded_component` observation ID. Device, area, and label targets are typed `ref1_` tokens. A missing target observation is a reference-only target, not an inferred observation.

Relationship identifiers use `rel1_` plus SHA-256 over framed domain, installation scope, predicate, source reference, and target reference. Cross-installation relationships and inferred references are invalid.

## 12. Ordering and duplicates

Observations are sorted lexicographically by observation ID and relationships by relationship ID. Identical normalized inputs collapse to one object. Conflicting payloads for one identity invalidate the affected capability snapshot; traversal order never resolves a conflict.

## 13. Lifecycle semantics

Rename of an authoritative key changes identity. Removal means absence from the current snapshot and never implies failure. Recreation with the same authoritative key reuses identity, but object continuity must not be inferred. Migration preserving the raw installation scope preserves identity; a scope change changes all scoped identities.

## 14. Invalid and absent inputs

Missing required input, invalid Unicode, an unknown category/capability pair, malformed source identifier, or conflicting duplicate is invalid. Invalid rows do not produce observations or relationships. Partial capability results must remain explicitly partial; the collector must not invent substitutes.

## 15. Privacy

Exported scopes and references are pseudonymous, not anonymous. Secret or personal fields remain excluded. Stable hashes may permit dictionary testing of low-entropy identifiers, bounded here by installation-scoped hashing and exclusion of raw identifiers. Consumers must not treat tokens as credentials or globally correlatable identities.

## 16. Stability and versioning

The identity algorithm is versioned by the `ck1`, `is1_`, `ref1_`, `obs1_`, and `rel1_` namespaces and explicit domain strings. Changes to canonical inputs, framing, normalization, hashing, or scope are identity-breaking and require governed architecture and contract treatment. Additive payload fields do not change identity.

## 17. Collision policy

SHA-256 collision is not resolved by suffixing or order. If one identifier maps to unequal canonical input tuples, the affected snapshot is invalid and activation must fail safely. This preserves determinism and makes collision handling explicit.

## 18. Governance outcome

The proposal closes the documented identity ambiguity without changing frozen scope. It recommends retaining Collector Contract `1.0.0` because no producer or consumer adoption has occurred; R-003 must decide the amendment and version consequence. DF-003 must establish any revised implementation baseline. Approval is not claimed by AI-001.

