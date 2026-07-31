# DF-001 Implementation Baseline

Implementation status: `NOT STARTED`

## Approved implementation scope

Release 1 may implement only:

1. Read-only API availability collection from `GET /api/`.
2. Loaded component identifiers from `GET /api/components`.
3. Registered event type identifiers from `GET /api/events`, excluding listener counts and event payloads.
4. WebSocket feature negotiation from `supported_features`.
5. Optional enabled-entity display references from `config/entity_registry/list_for_display`, subject to the frozen privacy gate.

The approved public producer contract is `hadocs-generic-metadata` 1.0.0. Its observation envelope, capability statuses, compatibility policy, deterministic ordering, provenance requirements and semantic prohibitions are fixed.

## Approved models

- Observation model: five contract-bound Release 1 categories.
- Relationship model: `entity_uses_platform`, `entity_assigned_to_device`, `entity_assigned_to_area`, and `entity_has_label`.
- Privacy model: field minimization, mandatory secret exclusion, fail-closed treatment, and installation-scoped non-reversible references for sensitive joins.
- Lifecycle: capability negotiation, bounded read collection, normalization, immutable snapshots, explicit partial/stale status, replacement refresh and graceful shutdown.
- Version strategy: independent Core, producer and contract versions; per-capability negotiation; additive-minor tolerance; major-version rejection.

## Approved implementation notes

The following notes are recorded exactly from R-001:

| Note | Classification |
|---|---|
| Minimum Core version capability matrix | Implementation |
| Opaque reference security review | Implementation |
| Implementation defaults | Operational |

No Documentation note remains open. These notes do not authorize expansion of architecture or Release 1 scope.

## Exclusions

No state/history/event-payload interpretation, diagnostics, health, failure, connectivity, HASK matcher, Consumer Contract, PI2, scoring, UI or recovery behavior is approved by this baseline.

