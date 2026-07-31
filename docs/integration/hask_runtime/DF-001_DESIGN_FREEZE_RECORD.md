# DF-001 Design Freeze Record

Design Freeze date: 2026-07-24

## Official baseline

| Item | Frozen value |
|---|---|
| Collector name | Generic Metadata Collector |
| Architecture Status | `FROZEN` |
| Collector Contract | `hadocs-generic-metadata` 1.0.0 |
| Observation Model Version | Not independently versioned; frozen as part of Collector Contract 1.0.0 |
| Relationship Model Version | Not independently versioned; frozen as part of Collector Contract 1.0.0 |
| Implementation Status | `NOT STARTED` |
| Architecture Review | `R-001` — `PASSED` |
| Review conclusion | `DESIGN_FROZEN_WITH_IMPLEMENTATION_NOTES` |
| Governance record | `DF-001` |

## Frozen architecture references

- `GENERIC_METADATA_COLLECTOR_SPECIFICATION.md`
- `GENERIC_METADATA_COLLECTOR_ARCHITECTURE.md`
- `GENERIC_METADATA_COLLECTOR_CONTRACT_SPECIFICATION.md`
- `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md`
- `GENERIC_METADATA_COLLECTOR_RELATIONSHIP_MODEL.md`
- `GENERIC_METADATA_COLLECTOR_PRIVACY_MODEL.md`
- `GENERIC_METADATA_COLLECTOR_LIFECYCLE.md`
- `GENERIC_METADATA_COLLECTOR_ERROR_MODEL.md`
- `GENERIC_METADATA_COLLECTOR_VERSION_STRATEGY.md`
- `GENERIC_METADATA_COLLECTOR_RELEASE_PLAN.md`
- `GENERIC_METADATA_COLLECTOR_IMPLEMENTATION_READINESS.md`

Architecture approval is recorded by `DESIGN_FREEZE_DECISION.md`, `ARCHITECTURE_REVIEW_FINAL_REPORT.md`, and `ARCHITECTURE_REVIEW_FINAL_STATE.json`.

## Frozen Release 1 scope

Approved capabilities are REST `GET /api/`, REST `GET /api/components`, restricted REST `GET /api/events`, WebSocket `supported_features`, and optional WebSocket `config/entity_registry/list_for_display`.

Approved observation categories are `api_availability`, `loaded_component`, `registered_event_type`, `websocket_feature`, and optional `entity_display_reference`.

## Binding statement

Future implementation shall conform exactly to the frozen specification and public producer contract 1.0.0. No architectural modification is permitted without a new Architecture Increment, Architecture Review, and Design Freeze.

