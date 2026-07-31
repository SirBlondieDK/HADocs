# Generic Metadata Collector Specification

Status: specification only  
Public contract target: `hadocs-generic-metadata` 1.0.0  
Discovery baseline: Home Assistant Core 2026.7.3

Amendment authority: A-001 removes `websocket_feature` and WebSocket `supported_features` from Release 1; no replacement is added.

## Purpose and boundaries

The future collector produces immutable snapshots of explicit Home Assistant metadata for downstream consumers. It is read-only, generic, implementation-independent, and inference-free. It does not diagnose, score, recommend, interpret state or history, inspect event payloads, or confirm causes.

The official capability inventory contains 50 capabilities. Thirteen were assessed as generically collectable; that label means technically collectable, not automatically suitable for Release 1.

## Release 1 collection policy

| Capability | Policy | Public observation | Reason |
|---|---|---|---|
| `GET /api/` | collect | `api_availability` | Explicit API response; lifecycle metadata only. |
| `GET /api/components` | collect | `loaded_component` | Explicit loaded component identifiers. |
| `GET /api/events` | collect with field restriction | `registered_event_type` | Export event type; omit runtime listener count. |
| `config/entity_registry/list_for_display` | optional | `entity_display_reference` | Documented compact enabled-entity topology; sensitive identifiers must be tokenized. |
| `GET /api/calendars` | future | none | Context-dependent and sensitive; low stability value. |
| `get_panels` | future | none | Documented purpose but response schema is elided. |
| `validate_config` | future/on demand | none | Requires caller-supplied configuration and is not passive metadata. |
| `extract_from_target` | future/on demand | none | Requires supplied target and exposes sensitive references. |
| three target capability commands | future/on demand | none | Input-dependent, sensitive, and not snapshot metadata. |
| `homeassistant/expose_entity/list` | future/optional | none | Sensitive and absence does not mean false. |

Existing HADocs collection of config, services, states and full registries is not reimplemented. A future implementation may adapt authoritative, allowlisted metadata already collected, but the public contract must not export state values, arbitrary attributes, undocumented registry fields, location data, secrets, names, or configuration values.

## Collection rules

1. Call only officially documented read-only interfaces.
2. Use an explicit capability and field allowlist.
3. Export only fields classified `AUTHORITATIVE`.
4. Preserve API provenance, collection status and Core version.
5. Never infer absence, health, connectivity, ownership, or causality.
6. Represent partial and unsupported collection explicitly.
7. Canonically order objects and arrays before serialization.

## Normalization

- Component, service and event identifiers retain the exact documented identifier and are compared case-sensitively.
- Sensitive Home Assistant identifiers become stable, installation-scoped opaque references before export.
- Relationships use those same opaque references.
- Missing optional fields remain absent; `null`, empty, false and missing are never collapsed.
- Unknown fields are ignored, counted in internal collection diagnostics, and never copied into observations.
- Duplicate observations with identical category and canonical key collapse deterministically; conflicting values make the capability partial.

## HASK opportunities

Potential future domains are component/service presence, event registration, explicit entity topology, target integrity, configuration validation and exposure policy. These are opportunities only: no matcher, claim, recommendation or cause is defined here. UniFi and MikroTik connectivity remain unsupported because no official standardized connectivity field exists.

## Non-goals

No implementation, schema, API client, subscription, diagnostic extraction, state interpretation, history interpretation, event-payload interpretation, HASK change, Consumer Contract change, PI2 change, scoring, UI, test or fixture is part of this increment.
