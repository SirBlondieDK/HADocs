# Architectural Risk Register

| ID | Risk | Class | Frozen mitigation | Residual level | Freeze impact |
|---|---|---|---|---|---|
| R-001-01 | Unversioned Home Assistant capability evolves | Version | Per-capability negotiation; required-field rejection; unknown-field ignore; explicit unsupported status | Medium | Non-blocking |
| R-001-02 | Sensitive identifiers become correlatable | Privacy | Installation-scoped, non-reversible, collision-resistant opaque references; no cross-installation equality | Medium pending security review | Non-blocking implementation gate |
| R-001-03 | Consumer interprets absence as failure | Semantic | Contract explicitly prohibits absence inference and exposes capability/scope status | Low | Non-blocking |
| R-001-04 | Partial and stale data are mixed | Lifecycle | Immutable snapshots; explicit stale flag; no invisible current/stale merge | Low | Non-blocking |
| R-001-05 | Undocumented fields leak into the contract | Authority/privacy | Closed allowlist and fail-closed unknown-field policy | Low | Non-blocking |
| R-001-06 | Entity display scope is mistaken for full registry | Semantic | Required `enabled_scope=true`; optional capability; absence non-diagnostic | Low | Non-blocking |
| R-001-07 | Implementation defaults create excessive load | Operational | Bounded reads/retries; cadence outside contract; operational review before activation | Medium | Non-blocking implementation gate |
| R-001-08 | Future release blurs snapshot and on-demand semantics | Extensibility | Release 2 requires a separate request/response contract | Low | Non-blocking |

No risk demonstrates a defect in the candidate architecture. Residual risks are controlled by frozen requirements and implementation gates.

