# Generic Metadata Collector Public Contract Specification

## Contract identity

- Name: `hadocs-generic-metadata`
- Initial version: `1.0.0`
- Versioning: semantic versioning of the public producer contract
- Encoding: UTF-8 JSON when serialized
- Canonical form: object keys lexicographically ordered; observation, relationship and capability arrays ordered by their canonical identities

This document specifies a contract, not a JSON Schema implementation.

## Envelope

| Field | Required | Meaning |
|---|---:|---|
| `contract_name` | yes | Exact contract name. |
| `contract_version` | yes | Producer contract version. |
| `snapshot_id` | yes | Opaque identity for this immutable snapshot. |
| `observed_at` | yes | UTC timestamp for the completed source snapshot. |
| `producer` | yes | Producer name and version, no environment paths. |
| `source` | yes | Home Assistant Core version and API surface identifiers. |
| `capabilities` | yes | Per-capability collection status. |
| `observations` | yes | Authoritative normalized observations, possibly empty. |
| `relationships` | yes | Explicit normalized relationships, possibly empty. |

Supervisor and OS versions are optional because their absence is not an error. Unknown values are represented as absent, never guessed.

## Observation envelope

Required fields: `observation_id`, `category`, `canonical_key`, `source_capability`, `source_api`, `observed_at`, `fields`, `privacy_treatment`, and `stability`.

Optional fields: `relationships`, `source_core_version`, and `scope`. Optional means consumers must tolerate absence. `fields` contains only the category-specific authoritative allowlist.

`observation_id` is stable for the same category and canonical key within one installation. Sensitive source identifiers must not be recoverable from it. The derivation algorithm is implementation-independent, but collision handling and installation scoping are mandatory.

## Capability status

Allowed status values are `success`, `partial`, `unsupported`, `permission_denied`, `unavailable`, `invalid_response`, and `authentication_expired`. A safe error code may accompany non-success status. Raw error messages, payloads and exception text are prohibited.

## Guaranteed behavior

- Every exported field is classified `AUTHORITATIVE`.
- Every observation names its documented source capability.
- Missing, `null`, empty and false remain distinct.
- Unknown fields are not exported.
- No observation asserts health, connectivity, cause, recommendation or score.
- Ordering and serialization are deterministic for identical normalized input and metadata.
- Major versions do not silently change existing semantics.

## Best-effort behavior

- Optional capability collection.
- Optional relationships when the source explicitly supplies them.
- Stable opaque references across snapshots when the same installation-scoped privacy context remains available.
- Continued operation after one capability fails.

## Undefined behavior

- Home Assistant response ordering.
- Meaning of undocumented fields.
- Integration-specific arbitrary attributes.
- Cross-installation equality of opaque references.
- Diagnostic meaning of presence or absence.
- Freshness beyond declared timestamps and capability status.

## Compatibility and deprecation

- Major: removes/renames a field, changes semantics, privacy treatment or identity rules.
- Minor: adds optional categories, fields, relationships or status metadata.
- Patch: clarifies wording without observable contract change.
- Consumers must ignore unknown optional fields and categories, but reject unsupported major versions.
- Deprecation is announced in a minor version; a deprecated element remains semantically stable until the next major version.

## Consumer expectations

Consumers validate the envelope and supported major version, honor per-capability status, keep snapshot provenance, treat observations as facts rather than findings, and never convert absence into a negative fact. Consumers must not reverse opaque references or persist internal source payloads.

