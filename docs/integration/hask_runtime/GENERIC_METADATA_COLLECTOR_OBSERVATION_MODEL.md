# Generic Metadata Collector Observation Model

Amendment authority: A-001 removes `websocket_feature` and WebSocket `supported_features` from Release 1; no replacement is added.

## Release 1 categories

| Category | Source | Required authoritative fields | Optional authoritative fields | Explicit exclusions | Potential HASK domain |
|---|---|---|---|---|---|
| `api_availability` | REST `GET /api/` | `available=true`, `source_api=REST` | none | response message text | collection provenance |
| `loaded_component` | REST `GET /api/components` | `component` | none | inferred integration status | component presence |
| `registered_event_type` | REST `GET /api/events` | `event_type` | none | `listener_count`, payloads | event registration |
| `entity_display_reference` | WS `config/entity_registry/list_for_display` | `entity_ref`, `platform`, `enabled_scope=true` | `device_ref`, `area_ref`, `label_refs`, `entity_category` | names, icons, display precision, arbitrary registry fields | topology and reference integrity |

`entity_display_reference` is optional in Release 1 because its identifiers are sensitive and the command returns enabled display entities rather than a complete registry. Its scope must always be present; consumers may not infer anything about disabled or absent entities.

## Field classification

Only `AUTHORITATIVE` fields above enter output. `STRUCTURED_CONTEXT` fields may be used internally to route or validate collection but are not serialized. `UNSAFE_INFERENCE` and `IGNORED` fields are discarded.

Examples:

- Event listener count: `STRUCTURED_CONTEXT`; a time-varying count is not needed by the metadata contract.
- API root message: `IGNORED`; availability is established by the successful documented response.
- Entity/device/area raw identifiers: `AUTHORITATIVE` source facts with mandatory privacy transformation into opaque references.
- Entity state and attributes: `IGNORED` for this collector.
- Undocumented registry fields: `IGNORED` regardless of live observation.

## Identity and lifecycle

An observation identity is the tuple `(category, canonical_key, installation_scope)`. A snapshot contains at most one observation for that identity. Observations are immutable within a snapshot. Across snapshots they are replaced as a whole, not patched. Disappearance means only “not present in this successful snapshot scope”; it is not deletion, failure or unavailability.

## Stability labels

- `documented_unversioned`: documented current API without a formal field-version guarantee.
- `documented_compact_optional`: documented compact payload with optional fields.
- `contract_stable`: normalized semantics guaranteed by this contract major version.

Source stability and contract stability are separate. The producer absorbs compatible source evolution and reports incompatible responses explicitly.
