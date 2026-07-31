# Native Connectivity Observation Blocker Report

## Decision

The Native Integration Connectivity Observation increment is formally blocked before production implementation.

The applicable stop condition is:

> Home Assistant does not expose a suitable generic structured signal.

## Why the available config-entry signal is insufficient

`config_entries/get` is authoritative for entry identity and lifecycle. It does not state that a connection test occurred or identify its result. Mapping lifecycle states to connectivity would create false semantics:

- setup errors can be import, migration, code, validation, dependency, authentication, or connection failures;
- setup retry means the entry is not ready, not necessarily that its target is unreachable;
- loaded does not prove a standardized connectivity test;
- reasons are integration-defined text or translation identifiers.

Consequently, a native observation with `connection_result=failed` and `problem_signal=true` cannot be created generically from this endpoint.

## Other reviewed sources

- Integration diagnostics: optional and integration-specific; no common schema.
- System Health: optional arbitrary keys; no config-entry association or common connectivity field, and no reviewed UniFi/MikroTik System Health implementation.
- Repairs: structured issues but integration-specific meaning; no common connection result.
- Manifests: identity and static capabilities only.
- Entity/device/state data: indirect symptoms only.
- Logs: free text and therefore prohibited.

## Preservation result

- Production source changes: 0
- PI1 runtime changes: 0
- HASK changes: 0
- Consumer Contract changes: 0
- HASK matcher calls: 0
- Candidates created: 0
- Confirmed candidates: 0
- Health Score changes: 0
- Existing tests: 251 passed

No observation model or collector was created because doing so without a valid source would produce a misleading contract with no truthful positive input.

## Required upstream capability

The smallest safe unblock is an official structured Home Assistant field or endpoint that reports an integration/config-entry connection test with:

- config-entry ID;
- integration domain;
- explicit result;
- source timestamp or scan context;
- disabled/ignored distinction;
- standardized semantics independent of integration-specific strings.

Alternatively, Home Assistant could define a common typed diagnostics or System Health connectivity capability. That would be an upstream Home Assistant contract change and is outside this increment.

PI2 must not resume from this state.

