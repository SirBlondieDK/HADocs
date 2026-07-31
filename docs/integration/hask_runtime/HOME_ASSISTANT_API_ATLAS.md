# Home Assistant API Atlas

## Versioned scope

- Official documentation reviewed: current on 2026-07-24
- Live Home Assistant Core: 2026.7.3
- Supervisor and OS versions: unknown through the safely examined Core API surface
- Official capabilities: 50
- Live responses persisted: none

## Primary surfaces

WebSocket is the richer structured discovery surface for registries, target resolution, subscriptions, validation, and session features. REST remains useful for availability, components, event counts, history, logbook, calendars, configuration validation, and simple state/config/service snapshots.

The live atlas confirmed structural parity between REST/WS config and state snapshots. Service response containers differ: REST returned a list of domain objects while WebSocket returned a domain-keyed object.

Four successfully observed commands lacked independent official Developer-documentation confirmation and remain non-authoritative: floor registry, label registry, config-entry listing, and System Health. A Repairs command attempt returned `unknown_command` and proves nothing.

The complete reproducible atlas is [HOME_ASSISTANT_API_ATLAS.json](HOME_ASSISTANT_API_ATLAS.json).

