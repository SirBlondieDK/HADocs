# Generic Metadata Collector Specification Increment — Final Report

## Executive summary

The completed discovery has been converted into an implementation-independent architecture and public producer contract specification. The design deliberately narrows 13 technically generic capabilities to five Release 1 metadata sources, one of which is optional. This preserves authority and privacy instead of maximizing coverage.

## Defined architecture

The future producer uses capability negotiation, documented read-only adapters, a closed authoritative field gate, privacy transformation, deterministic normalization, immutable snapshots and canonical serialization. Failures are isolated per capability. Consumers receive facts with provenance, never findings or inferred meaning.

## Public contract

Contract `hadocs-generic-metadata` 1.0.0 defines the envelope, observation identity, capability status, explicit relationships, deterministic ordering, semantic versioning, deprecation and consumer obligations. It is a prose specification only; no schema or code was implemented.

## Release scope

- Release 1: API availability, loaded components, event types, WS features, optional enabled-entity display topology.
- Release 2: separately contracted on-demand validation, target and exposure operations.
- Release 3: separately governed temporal, subscription and future documented system interfaces.

Calendars, panels without field-level schema, runtime state, history, event payloads, diagnostics and connectivity are excluded from Release 1. UniFi/MikroTik connectivity remains unavailable from the reviewed authoritative API surface.

## Risks and open items

The main risks are unversioned upstream APIs, sensitive topology identifiers, schema-elided payloads and consumers overinterpreting absence. The specification addresses them through capability negotiation, opaque references, field allowlists, explicit scope and non-inference guarantees. A minimum Core version and concrete opaque-reference algorithm remain implementation-review items.

## Preservation result

This increment creates documentation only. It introduces no collector, runtime, API client, schema, test, fixture, HASK record, Consumer Contract change, matcher, PI2 wiring, score, UI or recovery behavior.

## Final conclusion

`READY_WITH_MINOR_OPEN_ITEMS`

The conclusion is based on the frozen 50-capability discovery inventory, the 13-capability generic assessment, the documented/observed field classifications and the explicit lack of a standardized connectivity signal.

