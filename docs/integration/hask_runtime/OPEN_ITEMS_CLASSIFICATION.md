# Open Items Classification

Each item is assigned exactly one R-001 class.

| Open item | Classification | Reason | Required closure |
|---|---|---|---|
| Minimum Core version capability matrix | Implementation | The architecture intentionally negotiates capabilities instead of asserting an unsupported global minimum. The matrix validates concrete implementations and tested versions. | Record tested versions and per-capability outcomes before production support is claimed. |
| Opaque reference security review | Implementation | Contract-level requirements—installation scope, non-reversibility, collision resistance and stability—are frozen. Selecting and proving a compliant mechanism is implementation work. | Independent security review and deterministic collision/privacy tests before entity references are enabled. |
| Implementation defaults | Operational | Refresh cadence, retry timing, cache location and enablement defaults operate within already specified bounds and do not alter public semantics. | Approve safe local defaults and resource limits before production activation. |

Architectural items: **0**. Therefore no listed open item blocks Design Freeze.

