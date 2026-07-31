# Final Discovery Report

## Conclusion

`GENERIC_COLLECTOR_REQUIRED`

The official inventory contains 24 HTTP and 26 WebSocket capabilities. Live, read-only structural sampling on Core 2026.7.3 confirmed major config/state/service/registry schemas without persisting credentials, values or raw responses.

HADocs already covers 18% of the documented surface. Thirteen additional capabilities can be collected generically and safely, primarily validation, targets, component/event inventories, display registry, panels and exposure settings. This justifies the program-wide conclusion.

The conclusion does not apply to UniFi/MikroTik connectivity: those remain blocked because no documented explicit connection-result contract exists. Four observed-undocumented commands were excluded from authoritative design.

No production code, collector, runtime, test, fixture, HASK record, schema, Consumer Contract or matcher was changed. The atlas is planning evidence only.

