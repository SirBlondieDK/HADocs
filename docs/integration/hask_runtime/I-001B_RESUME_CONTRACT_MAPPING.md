# I-001B_RESUME Contract Mapping

## Common required envelope

Every observation requires `observation_id`, `category`, `canonical_key`, `source_capability`, `source_api`, `observed_at`, `fields`, `privacy_treatment`, and `stability`. Optional fields are `relationships`, `source_core_version`, and `scope`.

The contract defines conceptual identity as `(category, canonical_key, installation_scope)` and requires stable identity across snapshots within an installation.

## Mapped fields

- `api_availability`: source and fields are defined; canonical key is not defined.
- `loaded_component`: component is defined; the contract does not explicitly designate it as the canonical key.
- `registered_event_type`: event type is defined; the contract does not explicitly designate it as the canonical key.
- `entity_display_reference`: opaque entity reference is defined; its relationship to canonical key and installation scope is not explicitly fixed.

## Relationship mapping

The four predicates, explicit-source rule, optional cardinalities, reference-only resolution and absence semantics are defined. Their endpoint references ultimately depend on the unresolved observation/reference identity contract.

## Blocking gap

No frozen artifact defines:

- the category-specific canonical key for each of the four observations;
- the normative public encoding of `observation_id`;
- the source and representation of `installation_scope` used for stable identity;
- whether `source_capability` uses an endpoint/command string or an internal canonical capability ID.

Those choices affect public bytes, deduplication, relationship targets and cross-snapshot joins. They cannot be selected as implementation defaults.

