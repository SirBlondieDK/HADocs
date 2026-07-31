# I-001B_RESUME Blocker Report

## Conclusion

`RELEASE_1_RESUME_BLOCKED`

## Affected scope

- Capability: all four Release 1 capabilities
- Observation: all four observation categories
- Fields: `observation_id`, `canonical_key`, `source_capability`
- Relationships: endpoint identity for the four frozen predicates

## Frozen text boundary

`GENERIC_METADATA_COLLECTOR_CONTRACT_SPECIFICATION.md` requires `observation_id` and `canonical_key`, requires identity stability within an installation, and states that identity is based on category and canonical key. `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md` states the identity tuple `(category, canonical_key, installation_scope)`.

The four category definitions list authoritative payload fields but do not assign category-specific canonical keys or a normative observation-ID representation.

## Ambiguity

For `api_availability`, plausible canonical keys include `/api/`, `REST`, `api`, or a canonical capability identifier. For repeating observations, plausible keys include the authoritative payload value alone or a source-qualified form. The public `source_capability` value is likewise not enumerated. `installation_scope` is part of conceptual identity but has no defined source or public representation.

These alternatives produce different stable IDs, duplicate behavior, relationship references and serialized hashes. No option can be selected from DF-002 without interpretation.

## Implementation impact

The adapters cannot emit contract-conformant observations deterministically until identity semantics are frozen. Deferring identity to a caller or selecting an encoding in code would redefine the public contract and violate G-001.

## Work completed before discovery

- Governance and baseline verification completed.
- Historical blocker resolution recorded.
- Four-capability inventory completed.
- Source-to-contract field mapping completed up to identity.
- Production source changes: 0.
- Test and fixture changes: 0.

All completed documentation is independent and safe to retain.

## Smallest governance correction

Create a narrow Architecture Increment limited to the observation identity contract. It must define category-specific canonical keys, `observation_id` encoding guarantees, installation-scope handling, canonical `source_capability` values, and relationship endpoint identity. Then perform Architecture Review and a new Design Freeze before resuming implementation.

No other Release 1 semantic was reviewed after this blocker was found.

