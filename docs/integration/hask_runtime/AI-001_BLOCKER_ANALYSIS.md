# AI-001 Blocker Analysis

DF-002 requires stable `observation_id`, `canonical_key`, `source_capability` and installation-scoped identity, but leaves their byte-level construction incomplete.

The gap affects all four observations, duplicate resolution, cross-snapshot joins, all relationship references, canonical JSON bytes, privacy transformation, restore/clone behavior and consumer interoperability. Plausible keys and encodings yield different public output while each appears locally deterministic. Implementation therefore cannot choose safely.

The missing decisions are public semantics rather than algorithms hidden behind an equivalent interface. They require architecture because consumers compare identifiers, relationships depend on them, and later changes would alter serialized contract values.

AI-001 is limited to completing those identity semantics. It does not change capability, observation or predicate counts.

