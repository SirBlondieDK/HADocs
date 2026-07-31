# Live API Response Catalog

All calls were read-only and used the existing token from Windows Credential Manager in memory. No token or raw response was displayed or persisted.

Documented and observed REST capabilities:

- `/api/`: object
- `/api/config`: object
- `/api/states`: 1,023 items
- `/api/services`: 79 domain items
- `/api/events`: 28 event items
- `/api/calendars`: 10 calendar items

Documented and observed WebSocket capabilities:

- `get_config`: object
- `get_states`: 1,023 items
- `get_services`: domain-keyed object
- `get_panels`: dynamic object; keys discarded
- entity registry: 1,648 items
- device registry: 178 items
- area registry: 18 items

Counts describe this installation at one scan time and are not knowledge claims. Only allowlisted field paths and types appear in the JSON catalogs.

