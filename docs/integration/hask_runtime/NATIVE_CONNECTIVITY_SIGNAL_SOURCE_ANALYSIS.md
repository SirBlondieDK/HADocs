# Native Connectivity Signal Source Analysis

## Required property

The increment requires a vendor-neutral Home Assistant source that explicitly states whether an integration or config entry established its expected connection. It must not require interpretation of entity availability, platform names, free text, or vendor-specific payloads.

## Sources reviewed

### Config entries

Home Assistant Core exposes `config_entries/get` through the WebSocket API. The serialized entry includes `entry_id`, `domain`, `state`, `disabled_by`, `reason`, translation metadata, and timestamps.

This is a stable and useful lifecycle source, but it is not a connectivity-result source:

- `loaded` means setup completed, not that a standardized connection test succeeded;
- `setup_error` includes import errors, integration exceptions, and setup returning false;
- `setup_retry` represents `ConfigEntryNotReady`, whose cause is integration-defined;
- `migration_error`, `failed_unload`, `not_loaded`, disabled, and ignored states are not connectivity failures;
- `reason` and translation keys are integration-defined and do not use a generic connectivity taxonomy.

Classifying `setup_error` or `setup_retry` as `connection_result=failed` would therefore be inference and would conflate lifecycle with connectivity.

Official implementation references:

- [Config-entry WebSocket endpoint](https://github.com/home-assistant/core/blob/dev/homeassistant/components/config/config_entries.py)
- [ConfigEntry states and serialized fields](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py)
- [Config-entry state transition note](https://developers.home-assistant.io/blog/2025/02/19/new-config-entry-states)

Access: WebSocket authentication; some config-entry operations require administrator permission. Version applicability: current Core `dev` source reviewed on 2026-07-24; individual states have changed over time.

### Integration diagnostics

The diagnostics API can return config-entry or device diagnostics when an integration implements them. The payload is deliberately integration-specific. Home Assistant requires integrations to redact sensitive data, but it defines no common field for connection result, error category, or connection-test provenance.

Generic consumption would either copy unknown fields, risking sensitive-data exposure, or require vendor-specific parsing. Neither is permitted.

Official reference: [Integration diagnostics](https://developers.home-assistant.io/docs/core/integration/diagnostics/).

### System Health

`system_health/info` groups arbitrary integration-provided keys under an integration domain. Integrations may expose endpoint reachability, and the framework provides a URL reachability helper. However:

- the returned keys and meanings are integration-defined;
- participation is optional;
- results are not associated with a config-entry ID by the generic contract;
- the reviewed Core tree has no System Health platform for UniFi or MikroTik;
- generic interpretation would require matching integration-specific keys.

The endpoint is therefore a possible future explicit source only if Home Assistant standardizes a connectivity field or the relevant integrations expose a common typed value.

Official references:

- [Integration System Health](https://developers.home-assistant.io/docs/core/integration_system_health)
- [System Health implementation](https://github.com/home-assistant/core/blob/dev/homeassistant/components/system_health/__init__.py)

### Repairs

`repairs/list_issues` exposes structured issue identity, domain, severity, translation key, placeholders, and lifecycle data. Issue IDs and translation semantics are integration-specific. There is no generic connectivity category or connection-result field. Using issue names or translations would be string-based inference.

Official reference: [Repairs WebSocket implementation](https://github.com/home-assistant/core/blob/dev/homeassistant/components/repairs/websocket_api.py).

### Integration manifests

Manifest data establishes an integration domain and capabilities such as config-flow support. It contains no runtime connection result. It is suitable for identity only.

Official reference: [Integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/).

### REST states, entity registry, and device registry

These sources identify entities, platforms, devices, and current entity state. They do not establish a config-entry connection attempt. `unavailable`, missing entities, and diagnostic-category entities remain indirect symptoms.

Official references: [REST API](https://developers.home-assistant.io/docs/api/rest/) and [WebSocket API](https://developers.home-assistant.io/docs/api/websocket/).

### Logs

Logs may contain integration-specific exception text, but free-text parsing, regex classification, and platform-specific string matching are explicitly prohibited. Logs were rejected without further implementation.

## Source-selection decision

No reviewed source provides all of the following generically:

- stable config-entry reference;
- structured integration domain;
- explicit connection attempt/result;
- standardized failed/succeeded/unknown/not-tested semantics;
- disabled/ignored separation;
- safe vendor-neutral error category.

Config entries provide identity and lifecycle but not connectivity. Diagnostics and System Health can contain connectivity data only through optional, integration-defined structures. Repairs provides typed issues but no generic connectivity meaning.

No source was selected.

