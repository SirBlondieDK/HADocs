# Native Connectivity Observation Preflight

## Decision

Preflight passed. Source discovery then reached the program's explicit stop condition because Home Assistant does not expose a suitable generic structured connectivity result for config entries or integrations.

## Preserved state

- Repository branch: `main`
- HEAD: `590cc33a9762c4d22699f20c60d136ef2c4de00c`
- Merge conflicts: 0
- Approved dirty baseline: verified through its frozen manifest
- Completed pilot: 0 unexpected mismatches
- Completed PI1 implementation: 0 unexpected mismatches
- Compatibility Test Increment: both approved test checksums match
- PI2 blocker boundary: 0 mismatches
- HASK authoritative tree changes during this increment: 0
- Consumer Contract changes during this increment: 0
- Confirmed candidates: 0
- Health Score changes: 0

## Tests

The complete HADocs suite passed before source selection:

```text
251 passed
```

The suite ran with Python 3.14, explicit repository and `src` import paths, bytecode writing disabled, pytest cache disabled, and an isolated temporary directory.

## Existing collection surface

HADocs currently collects states, Core configuration metadata, services, and entity/device/area/label registries. It does not collect config entries, integration diagnostics, Repairs issues, or System Health.

The existing transport supports generic authenticated REST GET and one-shot WebSocket calls. That capability is sufficient to call a new official endpoint, but no collector was added because no reviewed endpoint supplies the required generic connectivity semantics.

## Outcome

No production source, test, fixture, configuration, report API, PI1 runtime file, HASK file, or Consumer Contract file was changed. Only preflight and blocker documentation was added.

