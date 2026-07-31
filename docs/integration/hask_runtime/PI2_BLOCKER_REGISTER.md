# PI2 Blocker Register

| Scope | Status | Blocker | Unblock criterion |
|---|---|---|---|
| General PI2 evidence integration | blocked | No existing matcher has both complete executable semantics and a directly compatible signal already collected by normal HADocs scanning | Approve a separately scoped native-signal or authoritative matcher-contract increment that creates an exact pair without inference |
| UniFi connectivity | deferred | No explicit controller connection-test result | Stable typed result with config-entry reference, `unifi` domain, explicit outcome, state separation, scan context, and redacted metadata |
| MikroTik connectivity | deferred | No explicit API connection-test result | Stable typed result with config-entry reference, `mikrotik` domain, explicit outcome, state separation, scan context, and redacted metadata |
| Legacy log patterns | blocked | Scoped Home Assistant/Supervisor logs are not collected | Separately approved privacy-reviewed structured log-event collector; no free-text expansion or fuzzy matching |
| Legacy rules | blocked | Consumer Contract exports no closed required fields, normalization, conditions, outcomes, or canonical evidence target | Separate authoritative matcher-contract migration backed by an already compatible native signal |

This register is planning metadata. It does not authorize production implementation.
