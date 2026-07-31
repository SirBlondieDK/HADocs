# Generic Metadata Collector Relationship Model

## Principles

Relationships are exported only when an official response explicitly contains both endpoints or an explicit reference between them. No relationship is derived from names, domains, entity availability, naming conventions or shared attributes.

## Release 1 relationship types

| Relationship | Source | Cardinality | Notes |
|---|---|---|---|
| `entity_uses_platform` | entity display response | entity to component/platform identifier | Explicit `pl`; does not assert loaded health. |
| `entity_assigned_to_device` | entity display response | zero or one device reference | Optional `di`; opaque reference. |
| `entity_assigned_to_area` | entity display response | zero or one area reference | Optional `ai`; opaque reference. |
| `entity_has_label` | entity display response | zero or many label references | Optional `lb`; opaque references. |

Floor and config-entry relationships are reserved concepts, not Release 1 relationship types. The reviewed official Developer API did not provide an authoritative documented public command and field contract for them. Device, area and label references may therefore be unresolved targets in Release 1 and must carry `resolution=reference_only`.

## Relationship envelope

Required fields: `relationship_id`, `predicate`, `source_ref`, `target_ref`, `source_capability`, `observed_at`, and `resolution`. Identity is the canonical tuple `(predicate, source_ref, target_ref)`. Duplicate tuples collapse; contradictory cardinality makes the capability partial.

## Integrity rules

- References use the same opaque tokens as observations.
- Dangling references are allowed only with `resolution=reference_only`.
- Absence of a relationship never proves non-membership.
- Consumers must not synthesize reverse predicates as new facts; they may build read-only indexes.
- Relationship order has no semantics.

## Future relationships

Target resolution could later add explicit missing-device, missing-area, missing-floor and missing-label references, but only in an on-demand contract phase. Official future config-entry, floor or label interfaces may add new minor-version predicates after review. No undocumented live command is an acceptable source.

