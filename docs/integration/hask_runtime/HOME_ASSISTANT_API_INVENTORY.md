# Home Assistant API Inventory

The authoritative inventory contains 50 capabilities: 24 HTTP method/path pairs and 26 WebSocket command types. Query parameters do not create separate capabilities. Supervisor APIs and commands not explicitly present in current official Developer documentation are excluded.

REST includes API availability, Core config, components, events, services, history, logbook, states, error log, camera proxy, calendars, state/event/service/template/config-validation/intent operations, conversation, and authentication flows. WebSocket includes feature negotiation, events/triggers, states/config/services/panels, validation, target extraction/capability lookup, entity-display and exposure interfaces, three registry list commands documented by the official custom-dashboard example, and security-sensitive mutation/auth commands.

The complete operation-level inventory, fields, classification, privacy, HADocs status, observation status, and stability is [HOME_ASSISTANT_API_ATLAS.json](HOME_ASSISTANT_API_ATLAS.json).

Official sources:

- https://developers.home-assistant.io/docs/api/rest/
- https://developers.home-assistant.io/docs/api/websocket/
- https://developers.home-assistant.io/docs/auth_api/
- https://developers.home-assistant.io/docs/intent_conversation_api/
- https://developers.home-assistant.io/docs/api/native-app-integration/sending-data/
- https://developers.home-assistant.io/docs/frontend/custom-ui/custom-strategy/

The APIs are documented but unversioned. No general field-level compatibility guarantee is stated.

