# R-003 Relationship Reference Review

AI-001 preserves the four predicates and cardinalities, prohibits display-name inference, requires same-installation endpoints, permits only explicit source relationships, supports `reference_only`, collapses duplicate tuples and defines deterministic `rel1_` ordering and collision failure.

Compatibility defect: the frozen relationship model requires references to use the same opaque tokens as observations. The entity observation explicitly carries `entity_ref = ref1_entity_…`, yet AI-001 assigns `source_ref = obs1_…`. This changes the endpoint namespace and the public relationship identity tuple. The proposal does not establish that DF-002’s wording authorized replacement by an observation envelope ID.

Lifecycle after target absence remains reference-only; source observation removal removes the current relationship, but the matrix’s removal terminology is inconsistent.

Relationship-reference gate: **FAIL**.

