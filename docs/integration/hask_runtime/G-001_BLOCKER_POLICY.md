# G-001 Blocker Policy

## Mandatory blocker conditions

Stop implementation when completion would require any of:

- choosing between multiple contract meanings;
- inventing an observation, field, relationship or lifecycle semantic;
- inferring an authoritative fact from context or absence;
- weakening privacy or read-only guarantees;
- changing a frozen version or compatibility rule;
- using undocumented behavior as authority;
- expanding or replacing frozen scope;
- allowing consumer adoption before verification.

## Required blocker record

A blocker identifies the frozen requirement, the exact ambiguity or conflict, the affected scope, preservation status and the governance action required. It does not resolve the ambiguity in implementation.

## Resolution path

When the blocker demonstrates an architecture defect:

1. Architecture Increment
2. Architecture Review
3. New Design Freeze
4. Resumed implementation against the new baseline

A-001, R-002 and DF-002 are the historical example. Implementation convenience is never sufficient to bypass this path.

