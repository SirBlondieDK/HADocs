# PS-001 Dependency Roadmap

The roadmap is dependency-based. It assigns no dates, owners, estimates or completion percentages.

## I-001B — Release 1 Capability Implementation (resume)

- Purpose: implement only the four DF-002 Release 1 capabilities.
- Entry: active I-001B exception; G-001 followed; DF-002 verified; existing infrastructure preserved.
- Permitted work: frozen adapters, observations, relationships, privacy, normalization and deterministic serialization only.
- Exit: `RELEASE_1_IMPLEMENTED` or `RELEASE_1_IMPLEMENTED_WITH_NOTES`; ambiguity yields `IMPLEMENTATION_BLOCKED`.
- Blockers: any new semantic choice, undocumented API, privacy failure or frozen-baseline conflict.
- Successor: V-001.

## V-001 — Collector Contract Verification

- Purpose: independently verify producer conformance to contract 1.0.0 and DF-002.
- Entry: I-001B completed successfully.
- Permitted work: contract, privacy, determinism, read-only, version and regression verification under a separate exception.
- Exit: a separately defined successful verification conclusion.
- Blockers: contract mismatch, nondeterminism, privacy leakage, inference or regressions.
- Successor: K-001 only after PASS.

## K-001 — HASK Consumer Integration

- Purpose: integrate verified producer output with HASK under an approved consumer contract.
- Entry: V-001 successful; producer artifact and consumer behavior approved.
- Permitted work: separately authorized consumer integration only.
- Exit: a separately defined consumer-integration conclusion.
- Blockers: unverified implementation behavior, authority loss or contract mismatch.
- Successor: PI-001.

K-001 may not treat unverified implementation behavior as contract.

## PI-001 — Downstream Consumer or PI2 Integration

- Purpose: connect approved consumer behavior downstream.
- Entry: verified producer plus approved consumer integration.
- Permitted work and exit: must be defined by a future explicit exception.
- Blockers: missing V-001 PASS or incomplete K-001 authority preservation.
- Successor: not defined by current authority.

Consumer adoption is prohibited until V-001 passes.

