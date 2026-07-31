# PS-001 Generic Metadata Collector Program Status

## Executive status

The program has a permanent governance policy and a frozen implementation baseline. Infrastructure exists, but Release 1 capability implementation has not completed.

| Program fact | Current value | Authority |
|---|---|---|
| Governance policy | G-001 — permanent | `G-001_FINAL_STATE.json` |
| Implementation baseline | DF-002 — active | `DF-002_FINAL_STATE.json` |
| Collector Contract | `hadocs-generic-metadata` 1.0.0 | DF-002 |
| Architecture | `FROZEN` | DF-002 |
| Release 1 capabilities | 4 | DF-002 |
| Observation categories | 4 | DF-002 |
| Relationship predicates | 4 | DF-002 |
| Replacement capabilities/observations | 0 / 0 | DF-002 |
| Infrastructure | I-001A complete with notes | `I-001A_IMPLEMENTATION_STATE.json` |
| Release 1 implementation | Not completed | I-001B blocker record |

## Current blocker and next work

The original I-001B attempt concluded `IMPLEMENTATION_BLOCKED` because of `websocket_feature`. A-001 removed the unsafe observation, R-002 approved the amendment, and DF-002 froze the corrected scope. The prior blocker remains historical evidence; no active governance blocker now prevents a properly authorized resume.

Next permitted increment: **I-001B Release 1 Capability Implementation — resume against DF-002 under G-001**.

## Gates

V-001 contract verification requires completed I-001B. HASK or any other consumer adoption is prohibited until V-001 passes. K-001 and PI-001 are planned dependencies, not approved active implementations.

## Governance history

Discovery and specification established the candidate; R-001/DF-001 froze it; I-001A built infrastructure; I-001B exposed one ambiguity; A-001/R-002 resolved it; DF-002 became the active baseline; G-001 made the process permanent. DF-001 remains preserved historical governance.

PS-001 is informational and replaces neither G-001 nor DF-002.

