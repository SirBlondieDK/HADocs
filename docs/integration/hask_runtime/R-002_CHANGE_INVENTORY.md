# R-002 Change Inventory

Authority: A-001 `REMOVE_WEBSOCKET_FEATURE`

| Candidate artifact | Class | Exact change |
|---|---|---|
| `GENERIC_METADATA_COLLECTOR_SPECIFICATION.md` | `REMOVE_CAPABILITY` | Removed Release 1 `supported_features` row. |
| `GENERIC_METADATA_COLLECTOR_SPECIFICATION.md` | `REMOVE_OBSERVATION` | Removed `websocket_feature` mapping. |
| `GENERIC_METADATA_COLLECTOR_SPECIFICATION.md` | `REMOVE_FIELD` | Removed feature identifier from Release 1 normalization. |
| `GENERIC_METADATA_COLLECTOR_SPECIFICATION.md` | `UPDATE_REFERENCE` | Recorded A-001 authority. |
| `GENERIC_METADATA_COLLECTOR_ARCHITECTURE.md` | `UPDATE_REFERENCE` | Removed feature negotiation from approved source-preference language and recorded A-001. |
| `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md` | `REMOVE_OBSERVATION` | Removed the `websocket_feature` row. |
| `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md` | `REMOVE_FIELD` | Removed its exclusive `feature` and `value` fields with the row. |
| `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md` | `UPDATE_REFERENCE` | Recorded A-001 authority. |
| `GENERIC_METADATA_COLLECTOR_RELEASE_PLAN.md` | `REMOVE_CAPABILITY` | Removed WebSocket supported features from Release 1 inventory. |
| `GENERIC_METADATA_COLLECTOR_RELEASE_PLAN.md` | `UPDATE_COUNT` | Revised effective Release 1 capability count from five to four. |
| `GENERIC_METADATA_COLLECTOR_RELEASE_PLAN.md` | `UPDATE_REFERENCE` | Recorded A-001 authority. |
| R-002 governance state | `VERSION_RECORD` | Retains first producer contract version 1.0.0 for the corrected pre-implementation baseline. |

No other change class or candidate artifact was required. No replacement capability, observation, field or relationship was added.

