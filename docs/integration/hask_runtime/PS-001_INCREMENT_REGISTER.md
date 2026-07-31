# PS-001 Increment Register

| ID | Authoritative name | Program type | Primary status | Conclusion/evidence | Role | Authoritative artifact | Successor/dependency |
|---|---|---|---|---|---|---|---|
| D-001 | Home Assistant Structured API Capability Discovery & Live API Atlas | Architecture discovery | COMPLETE | `GENERIC_COLLECTOR_REQUIRED` | HISTORICAL_FOUNDATION | `FINAL_DISCOVERY_STATE.json` | S-001 |
| S-001 | Generic Metadata Collector Specification Increment | Architecture specification | COMPLETE | `READY_WITH_MINOR_OPEN_ITEMS` | HISTORICAL_CANDIDATE | `GENERIC_METADATA_COLLECTOR_FINAL_STATE.json` | R-001 |
| R-001 | Architecture Review & Design Freeze Increment | Architecture governance review | COMPLETE | `DESIGN_FROZEN_WITH_IMPLEMENTATION_NOTES` | HISTORICAL_REVIEW | `ARCHITECTURE_REVIEW_FINAL_STATE.json` | DF-001 |
| DF-001 | Design Freeze Record | Governance record | COMPLETE | `DESIGN_FREEZE_RECORDED` | HISTORICAL / SUPERSEDED_BASELINE | `DF-001_FINAL_STATE.json` | I-001A; superseded by DF-002 |
| I-001A | Generic Metadata Collector Infrastructure | Implementation increment | COMPLETE | `INFRASTRUCTURE_IMPLEMENTED_WITH_NOTES` | IMPLEMENTED_INFRASTRUCTURE | `I-001A_IMPLEMENTATION_STATE.json` | I-001B |
| A-001 | Architecture Defect Resolution | Architecture defect resolution | COMPLETE | `REMOVE_WEBSOCKET_FEATURE` | HISTORICAL_DEFECT_AUTHORITY | `A-001_FINAL_STATE.json` | R-002 |
| R-002 | Architecture Amendment Review | Narrow architecture amendment review | COMPLETE | `AMENDMENT_APPROVED_WITH_IMPLEMENTATION_NOTES` | HISTORICAL_AMENDMENT_REVIEW | `R-002_FINAL_STATE.json` | DF-002 |
| DF-002 | Updated Design Freeze Record | Governance record | COMPLETE | `UPDATED_DESIGN_FREEZE_RECORDED` | ACTIVE_IMPLEMENTATION_BASELINE | `DF-002_FINAL_STATE.json` | I-001B resume |
| G-001 | Governance Preservation Policy | Permanent governance establishment | COMPLETE | `PERMANENT_GOVERNANCE_ESTABLISHED` | ACTIVE_GOVERNANCE_POLICY | `G-001_FINAL_STATE.json` | Governs all future increments |
| I-001B | Generic Metadata Collector Release 1 Capability Implementation | Contract-driven implementation | BLOCKED | `IMPLEMENTATION_BLOCKED` | NEXT_PERMITTED_RESUME; prior blocker resolved by DF-002 | `IMPLEMENTATION_SCOPE_BLOCKER.md` | Resume, then V-001 |
| V-001 | Collector Contract Verification | Verification increment | PLANNED | No artifact yet | VERIFICATION_GATE | none | Requires completed I-001B; gates K-001 |
| K-001 | HASK Consumer Integration | Consumer integration | PLANNED | No artifact yet | CONSUMER_GATE | none | Requires successful V-001; precedes PI-001 |
| PI-001 | Downstream Consumer or PI2 Integration | Downstream integration | PLANNED | No artifact yet | DOWNSTREAM_GATE | none | Requires verified producer and approved consumer behavior |

`COMPLETE` records execution conclusion; role separately records whether a completed baseline is active or superseded. Planned entries are roadmap placeholders only and are not implementation approvals.

