# R-003 Category Profile Review

| Category | Source / canonical component | Vector result | Lifecycle/privacy result | Verdict |
|---|---|---|---|---|
| `api_availability` | `rest.api_root`; fixed `rest_api_root` | reproduced | fixed identity; missing response means absence | PASS |
| `loaded_component` | `rest.components`; exact NFC component | reproduced | rename/recreate rules clear; removal conflicts with matrix | FAIL |
| `registered_event_type` | `rest.events`; exact NFC event type | reproduced | rename/recreate rules clear; removal conflicts with matrix | FAIL |
| `entity_display_reference` | documented compact entity ID transformed to `ref1_entity_` | reproduced | transformation violates frozen secret-material guarantee; relationship source changes token family; removal conflict | FAIL |

Prohibited components, installation scope, invalid input, migration and key construction are otherwise explicit. All four categories must pass for approval.

Category profiles passed: **1 of 4**. Category-profile gate: **FAIL**.

