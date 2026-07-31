# AI-001 Source Capability Specification

`source_capability` is a required public ASCII string from this closed vocabulary:

| Observation category | Value | Authoritative operation |
|---|---|---|
| `api_availability` | `rest.api_root` | REST `GET /api/` |
| `loaded_component` | `rest.components` | REST `GET /api/components` |
| `registered_event_type` | `rest.events` | REST `GET /api/events` |
| `entity_display_reference` | `websocket.entity_registry.list_for_display` | WebSocket `config/entity_registry/list_for_display` |

Grammar: `[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)+`. Values are lowercase and case-sensitive. Aliases, unknown values, adapter names and endpoint variants are prohibited.

`source_capability` is serialized exactly as listed. It does not participate in `canonical_key`; it does participate in `observation_id`. An unsupported approved capability produces status `unsupported` and no observation. An adapter attempting an unknown value fails validation as `invalid_response` before publication.

Adding a future vocabulary value is an additive contract-minor candidate requiring governance. Renaming or removing a value changes observation IDs and is a major-version candidate. AI-001 changes no contract version.

