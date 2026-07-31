# G-001 Development Lifecycle

All future increments follow this ordered lifecycle:

1. **Architecture definition** — establish authoritative sources, semantics, scope, privacy, versioning and exclusions.
2. **Architecture review** — verify completeness, consistency and implementation readiness without coding.
3. **Design Freeze** — record the exact authoritative implementation baseline.
4. **Implementation** — implement only the frozen scope under an explicit implementation exception.
5. **Verification** — prove contract compliance, deterministic behavior, privacy, read-only boundaries and absence of regressions.
6. **Consumer adoption** — permit downstream use only after verification succeeds and provenance remains traceable to the active freeze.

If ambiguity appears at step 4 or 5, work stops. A demonstrated architecture defect returns through Architecture Increment, review and a new Design Freeze; implementation does not patch semantics locally.

Historical sequence A-001 → R-002 → DF-002 is the reference example. It is evidence of the process, not a modification of those records.

