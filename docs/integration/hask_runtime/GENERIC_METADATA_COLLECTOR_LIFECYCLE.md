# Generic Metadata Collector Lifecycle

## States

`inactive -> negotiating -> collecting -> normalizing -> ready`

Any active phase can yield `partial` or `failed` for an individual capability. Shutdown produces `inactive`. Lifecycle state describes the collector only and is never a Home Assistant root cause.

## Collection modes

- **Startup snapshot:** optional, after authenticated API availability is established.
- **Manual refresh:** explicit request for a complete new snapshot.
- **Scheduled refresh:** optional and configurable; cadence is not a contract guarantee.
- **Subscription:** excluded from all releases of this generic snapshot collector unless separately specified.

## Snapshot rules

Collection uses a bounded observation window. Each capability records its own observation time. The snapshot becomes immutable only after normalization and privacy checks. Refresh creates a new snapshot; it never mutates the active one in place.

## Cache and staleness

A cache is optional, read-only to consumers, and stored outside source/bundle directories. Cache identity includes contract version, Core version, capability set and normalized content checksum. Staleness is explicit through `observed_at` and optional `stale_since`; no fixed freshness guarantee is imposed by the contract.

On refresh failure, the last valid snapshot may remain available with `stale=true`. Consumers must be able to reject stale data. Current and stale capability results are never silently combined.

## Activation and shutdown

Activation requires a valid supported contract snapshot; partial capability status is allowed. Graceful shutdown cancels no Home Assistant work because only bounded read requests are used. Credentials, transient payloads and raw errors must not be serialized during shutdown.

