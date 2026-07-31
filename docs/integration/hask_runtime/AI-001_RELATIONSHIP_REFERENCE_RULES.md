# AI-001 Relationship Reference Rules

No predicate is added or changed.

## Endpoint references

- `source_ref` for all four predicates is the entity observation's `observation_id`.
- `entity_uses_platform.target_ref` is the deterministic `loaded_component` observation ID computed from the explicit platform identifier, even if that target observation is absent; absent target uses `resolution=reference_only`.
- Device, area and label targets use typed opaque tokens:
  `ref1_<kind>_<digest>`, where kind is `device`, `area`, or `label`, and digest is SHA-256 of `frame("hadocs-generic-metadata/source-reference/v1") || frame(installation_scope) || frame(kind) || frame(NFC(raw_id))`.
- Raw target identifiers and canonical keys are not duplicated in relationship output.

All endpoints must use the same installation scope. Cross-installation relationships are prohibited. A malformed reference invalidates the relationship; it does not invalidate an independently valid observation. Dangling targets are allowed only with frozen `resolution=reference_only`; absence proves nothing.

## Relationship identity

`relationship_id` is `rel1_` plus lowercase SHA-256 of:

```text
frame("hadocs-generic-metadata/relationship-id/v1") ||
frame(installation_scope) || frame(predicate) ||
frame(source_ref) || frame(target_ref)
```

Grammar is `rel1_[0-9a-f]{64}`. Equal `(predicate, source_ref, target_ref)` collapses. Unequal data with the same digest invalidates the new snapshot. Sort relationships lexicographically by UTF-8 bytes of `relationship_id`. Reverse indexes are derived only and never new facts.

