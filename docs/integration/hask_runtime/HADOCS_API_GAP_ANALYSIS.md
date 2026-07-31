# HADocs API Gap Analysis

HADocs consumes 9 of 50 documented capabilities: REST config/states/services, their WebSocket equivalents at the capability level, and entity/device/area registry lists.

Thirteen capabilities are suitable for a future generic read-only collector, including API availability, components, event inventory, calendars, WS feature negotiation, panels, validation, target extraction/capabilities, display registry and explicit exposure overrides.

Four require dedicated collectors: history, configuration validation and the two subscription models. Eight are blocked by privacy and sixteen are not relevant to diagnostic collection.

Current coverage is 18%; generic potential is 44%; maximum practical is 52%. No collector is implemented by this program.

