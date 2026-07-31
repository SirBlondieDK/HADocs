# DF-002 Implementation Baseline

Implementation status: `NOT STARTED`

## Approved Release 1 capabilities

1. REST `GET /api/` — API availability.
2. REST `GET /api/components` — loaded component identifiers.
3. REST `GET /api/events` — registered event types; listener counts excluded.
4. Optional WebSocket `config/entity_registry/list_for_display` — enabled entity display references subject to the frozen privacy gate.

## Approved observation inventory

- `api_availability`
- `loaded_component`
- `registered_event_type`
- `entity_display_reference` (optional)

## Approved relationship inventory

- `entity_uses_platform`
- `entity_assigned_to_device`
- `entity_assigned_to_area`
- `entity_has_label`

## Preserved models

- Producer contract: `hadocs-generic-metadata` 1.0.0.
- Privacy: fail-closed field minimization and reviewed installation-scoped opaque references for sensitive joins.
- Lifecycle: capability negotiation, bounded reads, normalization, immutable snapshots, explicit partial/stale state, replacement refresh and graceful shutdown.
- Versioning: independent source, producer and contract versions with per-capability negotiation and SemVer compatibility rules.

Replacement capabilities and observations: 0. Release 2 and Release 3 remain unchanged.

The existing implementation notes remain: minimum-Core capability matrix, opaque-reference security review and implementation defaults. They do not authorize architecture changes.

