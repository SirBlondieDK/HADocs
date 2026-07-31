# R-003 Versioning Review

## Recommendation

**INCREMENT_MAJOR_VERSION**

The frozen public contract states that changes to identity rules or privacy treatment are major-version changes. AI-001 does not merely clarify prose: it fixes serialized `canonical_key`, `installation_scope`, `source_capability`, `observation_id`, reference and relationship-ID algorithms. It also proposes a privacy transformation inconsistent with the frozen secret-material guarantee.

The absence of producer implementation, production data and consumer adoption reduces migration cost but does not erase the already frozen semantic-version policy. G-001 makes DF-002 authoritative until superseded; publication in a Design Freeze is sufficient governance exposure.

Rejected alternatives:

- `RETAIN_1.0.0`: contradicts explicit frozen identity/version rules.
- Patch: observable serialized semantics are not editorial.
- Minor: identity and privacy semantics are not additive optional fields.
- Blocked: evidence and version policy are sufficient for a recommendation.

R-003 does not change a version. A corrected architecture review and later Design Freeze must record the actual version outcome.

