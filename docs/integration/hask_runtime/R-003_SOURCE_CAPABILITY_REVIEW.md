# R-003 Source Capability Review

The vocabulary is closed and consistently used:

- `rest.api_root`
- `rest.components`
- `rest.events`
- `websocket.entity_registry.list_for_display`

Each maps one-to-one to a frozen category. Values are lowercase ASCII, dot-delimited, case-sensitive, alias-free and publicly serialized. Unknown values are invalid. Endpoint/command naming is architecturally justified because the field records exact source provenance and participates in identity. Future values require governed contract evolution.

Source-capability gate: **PASS**.

