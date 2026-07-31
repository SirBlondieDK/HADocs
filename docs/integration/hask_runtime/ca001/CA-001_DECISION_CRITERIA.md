# CA-001 Decision Criteria

## Purpose

These criteria define how later CA-001 alternatives will be compared. They do not prefer or select a primitive.

## Mandatory gates

An alternative is eligible only if it:

1. Uses secret local material as required by DF-002.
2. Produces deterministic, installation-scoped opaque references.
3. Defines all normative bytes without implementation discretion.
4. Keeps secrets and raw sensitive identifiers out of output and logs.
5. Prevents public installation scope from serving as the only private derivation input.
6. Provides explicit collision, invalid-input and fail-closed behavior.
7. Requires no network service or external key management.
8. Has a documented, interoperable specification suitable for independent implementations.
9. Supports explicit backup, migration, rotation, loss and recovery analysis.
10. Can be tested using deterministic synthetic vectors.
11. Does not modify active contract version, DF-002 or frozen prerequisite artifacts.

Failure of any mandatory gate rejects the alternative.

## Comparative dimensions

Eligible alternatives will be compared on:

- security margin and clarity of assumptions;
- resistance to dictionary confirmation and cross-installation correlation;
- standardization and multi-language interoperability;
- deterministic byte-level specification complexity;
- misuse resistance and parameter risk;
- output size and collision margin;
- secret generation, storage and validation burden;
- backup, restore, migration and rotation consequences;
- compatibility with existing identity namespaces;
- migration complexity and historical traceability;
- operational failure modes and recoverability;
- availability of independent implementations and synthetic-vector verification.

## Decision discipline

- Convenience alone is insufficient.
- Popularity alone is insufficient.
- Existing library availability cannot substitute for normative authority.
- Security claims must be scoped and attributable.
- Alternatives producing different bytes must be treated as distinct architectures.
- Residual risks and rejected alternatives must be recorded.
- The final recommendation must be exactly one complete architecture, but only a later approved CA-001 batch may make it.

## Tie and blocker rule

If two eligible alternatives remain materially equivalent and existing authority supplies no principled discriminator, CA-001 must state the explicit new architectural rationale used to choose, or stop if the active authority does not permit making that choice. The decision must never be delegated silently to implementation.
