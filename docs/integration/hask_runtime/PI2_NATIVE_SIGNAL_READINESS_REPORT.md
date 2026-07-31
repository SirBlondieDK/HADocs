# PI2 Native Signal Readiness Report

## Status

`NOT_READY`

HADocs can retrieve structured config-entry lifecycle data, but it still cannot produce the explicit vendor-neutral connectivity result required by the approved UniFi and MikroTik matcher contracts.

UniFi and MikroTik domains can be preserved from the structured config-entry `domain` field. Their failed connectivity state cannot be represented without inference because Home Assistant supplies no standardized connection-result field for these entries.

PI2 should remain blocked. A new PI2 Resume exception is not warranted until an explicit upstream signal or separately approved source contract exists.

