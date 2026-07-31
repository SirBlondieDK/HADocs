# CA-001 Existing Authority

## Status

This document inventories inherited authority. It introduces no cryptographic architecture decision.

## Governance hierarchy

| Authority | Binding effect on CA-001 |
|---|---|
| G-001 | Architecture precedes implementation; ambiguity blocks; implementation cannot invent contract semantics; independent review precedes a new freeze. |
| G-002 | Repository state controls resume; completed deliverables are preserved; partial work is continued; missing work alone may be created. |
| DF-002 | Remains the active implementation baseline with `hadocs-generic-metadata 1.0.0`, four capabilities, four observation categories and four relationship predicates. |
| AI-001 | Immutable unapproved base proposal. Its canonical-key, source-capability and observation-ID rules remain evidence, not active baseline. |
| R-003 | Immutable review evidence. R003-F-001 establishes the secret-local-material incompatibility; the other four findings remain outside CA-001 correction work. |
| AI-002 | Immutable and BLOCKED. Its cryptographic gate records what inherited authority establishes and what remains undefined. |
| CA-001 authority | Permits architecture documentation only for the cryptographic observation/reference identity ambiguity. |

## Inherited cryptographic requirements

The frozen Privacy Model requires opaque references that are deterministic within an installation privacy scope, non-reversible without secret local material, collision-resistant, stable enough for cross-snapshot joins and non-correlatable across installations. Secret material and raw-to-opaque mappings remain outside exported artifacts and logs.

Unsafe transformation fails closed for the affected capability. Raw sensitive identifiers are never a public fallback. The active contract requires stable installation-scoped opaque references and prohibits recovery of sensitive source identifiers from public identity output.

R-003 established that AI-001's unkeyed use of a public installation-scope token permits dictionary confirmation and does not satisfy the frozen secret-local-material requirement.

## Preserved boundaries

- DF-002 and contract version `1.0.0` remain active and unchanged.
- CA-001 does not activate a new contract or identity format.
- AI-001, R-003 and AI-002 remain unchanged.
- Production code, tests, fixtures, dependencies and configuration remain outside scope.
- Clone classification, relationship `source_ref`, removal semantics and major-version correction remain AI-002 matters and are not decided here.
- R-004, DF-003, I-001B_RESUME_2 and V-001 remain unauthorized.

## Authority gap carried into CA-001

Inherited authority specifies security properties but does not select a keyed primitive, secret representation, normative cryptographic bytes, format version, recovery model or test vectors. Those are the bounded architecture questions CA-001 may evaluate and later propose; this inventory does not answer them.

