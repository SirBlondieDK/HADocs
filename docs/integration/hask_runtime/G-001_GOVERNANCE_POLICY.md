# G-001 Generic Metadata Collector Governance Policy

Status: permanent governance policy  
Effective date: 2026-07-24  
Authoritative implementation baseline: DF-002

## Mandatory principles

1. **Architecture precedes implementation.** Public semantics, scope and boundaries are specified and reviewed before code is authorized.
2. **Frozen baselines are authoritative.** The active Design Freeze governs implementation until formally superseded.
3. **Implementation follows Design Freeze.** Implementation realizes the frozen baseline and does not reinterpret it.
4. **Ambiguity results in a blocker.** An implementation that cannot proceed without choosing public semantics stops and records the ambiguity.
5. **Architecture changes require governance.** A demonstrated defect requires an Architecture Increment, Architecture Review and new Design Freeze.
6. **Implementation cannot redefine contracts.** Code, tests, fixtures and operational defaults cannot add, remove or reinterpret public semantics.
7. **Verification precedes consumer adoption.** Contract compliance, determinism, privacy and preservation must pass before any consumer relies on an increment.

## Authority and duration

G-001 applies to all future Generic Metadata Collector implementation, verification and consumer increments. It remains binding unless a future governance increment explicitly supersedes it.

DF-002 remains the authoritative implementation baseline. G-001 governs how that baseline and future baselines are executed; it does not modify architecture or contract 1.0.0.

## Historical evidence

A-001 shows that an ambiguous observation must be resolved architecturally rather than guessed in code. R-002 shows the narrow review and amendment path. DF-002 shows that implementation resumes only after the corrected baseline is frozen.

