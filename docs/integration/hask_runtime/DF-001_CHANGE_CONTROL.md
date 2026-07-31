# DF-001 Change Control

## Governing rule

All future Generic Metadata Collector implementation increments shall reference DF-001 and conform to the frozen contract 1.0.0.

An implementation increment may choose mechanisms and operational defaults only within the frozen requirements. It may not redefine identities, observations, relationships, privacy guarantees, lifecycle semantics, version behavior, release boundaries or exclusions.

## Required architecture-change path

A deviation is permitted only when all of the following exist:

1. A demonstrated Architecture Defect.
2. An approved new Architecture Increment scoped to that defect.
3. An updated Architecture Review.
4. A new Design Freeze superseding DF-001 for the affected architecture.

Implementation convenience, stylistic preference, refactoring preference, performance speculation, or desire for broader scope is not sufficient justification.

## Compatibility control

Contract 1.0.0 remains the frozen producer baseline until superseded through the full change path. Additive implementation metadata is not automatically permitted: it must already be allowed by the frozen contract. Public semantic removal, reinterpretation, privacy weakening or identity changes require architecture governance and the contract-version consequences defined by the frozen version strategy.

## Traceability

Every implementation decision shall trace to DF-001, a frozen specification section, or one of the three approved implementation notes. Untraceable public behavior is out of scope.

