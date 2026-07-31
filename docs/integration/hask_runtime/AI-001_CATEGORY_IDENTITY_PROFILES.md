# AI-001 Category Identity Profiles

## `api_availability`

- Source capability: `rest.api_root`.
- Key component: fixed `rest_api_root`; key `ck1:api_availability:rest_api_root`.
- Prohibited: response message, URL, hostname, status text.
- Lifecycle: one identity per installation; success populates `available=true`.
- ID vector: `obs1_90cbe1026ff98c538ec18854829293d38349ca802779bc8d362e948a9481dbcd` under the common test scope.
- Rename/recreation/migration: endpoint display/location changes do not affect identity; scope migration preserves; scope change changes.
- Relationships: none. Missing/invalid source: no observation.

## `loaded_component`

- Source capability: `rest.components`.
- Key component: exact NFC component string; example key `ck1:loaded_component:mqtt`.
- Prohibited: display name, integration status, traversal index.
- Granularity: one observation per distinct component identifier.
- ID vector: `obs1_79927229da53e5b9d0b9b2e503f769329d20e7a475285cb24553ee70e903e713`.
- Rename: identifier change means new identity. Removal removes it from that snapshot without asserting failure. Recreation with same identifier restores same ID; new identifier changes it.
- Relationships: may be the computed target observation for `entity_uses_platform`. Invalid component: affected capability partial/invalid; no observation.

## `registered_event_type`

- Source capability: `rest.events`.
- Key component: exact NFC event type; example `ck1:registered_event_type:state_changed`.
- Prohibited: listener count, event payload, traversal index.
- Granularity: one observation per distinct event type.
- ID vector: `obs1_864d18c0e05d48fc16c99ddd83fc371057b8b8612b0a4010ea6e02baa4046b79`.
- Rename/removal/recreation: same rules as component identity.
- Relationships: none. Invalid event type: no observation.

## `entity_display_reference`

- Source capability: `websocket.entity_registry.list_for_display`.
- Authoritative raw identity: documented compact `ei` entity identifier.
- Public entity reference:
  `ref1_entity_` plus lowercase SHA-256 of
  `frame("hadocs-generic-metadata/source-reference/v1") || frame(installation_scope) || frame("entity") || frame(NFC(raw_entity_id))`.
- Example raw synthetic ID `sensor.kitchen_temperature` yields `ref1_entity_d26423e92d0995348b23e8a0bab951fd9696898a0230020d11896033125b0f92`.
- Canonical key: `ck1:entity_display_reference:` plus that reference token.
- ID vector: `obs1_2916c20e0c01a5b72588d693da87368aafdf654d80ab083eca3a0c26bb40b3c3`.
- Prohibited: names, icons, unique IDs, user labels as text, configuration, state.
- Rename: entity identifier change changes identity. Removal is absence only. Recreation with same identifier reuses identity; consumers must not infer object continuity beyond identifier equality.
- Relationships: source is entity observation ID; explicit platform/device/area/label fields only. Missing raw entity ID invalidates the row; no inferred fallback.

All vectors use raw installation UUID `123e4567-e89b-42d3-a456-426614174000` and its public scope specified by AI-001.

