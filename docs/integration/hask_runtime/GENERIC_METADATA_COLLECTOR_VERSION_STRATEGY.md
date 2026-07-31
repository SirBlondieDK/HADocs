# Generic Metadata Collector Version Strategy

## Three independent versions

1. Home Assistant Core version identifies the observed source.
2. Collector producer version identifies the implementation.
3. Public contract version identifies consumer semantics.

No version may substitute for another.

## Home Assistant compatibility

The discovery was tested against Core 2026.7.3. The reviewed official APIs are current but generally unversioned, so no evidence-backed global minimum Core version is specified. Implementations negotiate each capability at runtime and report `unsupported` without treating it as an error.

Unknown response fields are ignored. Missing required fields reject only the affected capability. Optional fields remain optional. Undocumented commands or fields never become a compatibility fallback.

## Contract compatibility

Consumers accept supported major versions, tolerate additive minor fields/categories, and ignore unknown optional elements. Producers do not remove or reinterpret an existing field within a major version. Privacy strengthening that removes previously exported data requires a major version unless the field was explicitly optional and the semantic guarantee remains intact.

## Deprecation

A capability or field moves through `supported`, `deprecated`, then `removed`. Deprecation is documented in a minor release with replacement guidance when one exists; removal occurs only at a major boundary. Source API deprecation may cause an earlier capability status of `unsupported`, but never silent substitution with an undocumented API.

## Open item

The minimum supported Core version remains intentionally unspecified until official per-capability introduction/deprecation data or an implementation compatibility matrix exists. This does not block a capability-negotiated implementation.

