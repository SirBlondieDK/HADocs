# I-001B_RESUME Capability Inventory

The active DF-002 scope contains exactly four capabilities:

| Capability | Mechanism | Observation | Authoritative fields | Relationships | Privacy |
|---|---|---|---|---|---|
| REST `GET /api/` | Read-only REST snapshot | `api_availability` | `available=true`, `source_api=REST` | none | Response message excluded |
| REST `GET /api/components` | Read-only REST snapshot | `loaded_component` | `component` | none | LOCAL identifier preserved |
| REST `GET /api/events` | Read-only REST snapshot | `registered_event_type` | `event_type` | none | Listener count and payload excluded |
| Optional WebSocket `config/entity_registry/list_for_display` | Read-only WebSocket snapshot | `entity_display_reference` | `entity_ref`, `platform`, `enabled_scope=true`; optional `device_ref`, `area_ref`, `label_refs`, `entity_category` | Four frozen entity predicates when explicit source references exist | Raw identifiers require installation-scoped opaque transformation |

All observations require the common contract envelope, capability provenance, deterministic ordering, missing/null/empty/false preservation and frozen error/lifecycle behavior.

The retrieval scope is unambiguous. Observation identity values are not, so this inventory is not implementation authorization.

