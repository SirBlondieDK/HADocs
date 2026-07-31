# Generic Metadata Collector Release Plan

Amendment authority: A-001 removes `websocket_feature` and WebSocket `supported_features` from Release 1; no replacement is added.

## Release 1 — authoritative metadata snapshot

Capabilities: API availability, loaded components, registered event types, and optional enabled entity display references. Value: a small generic and privacy-bounded metadata surface. Risk: low to medium; entity reference privacy and compact optional fields require careful conformance. Complexity: low to medium. HASK opportunity: component/event presence and explicit topology only.

Release 1 excludes listener counts, states, history, event payloads, calendars, panels, validation and target commands.

## Release 2 — explicit on-demand metadata operations

Candidates: `validate_config`, `extract_from_target`, target trigger/condition/service commands, and explicit exposure overrides. `get_panels` may enter only after an authoritative field allowlist is established. Value: configuration and reference-integrity evidence. Risk: medium to high because requests contain sensitive caller input and absence semantics vary. Complexity: medium. HASK opportunity: validation and missing-reference domains, not causes.

Release 2 requires a separate request/response contract; it must not be silently folded into snapshot observations.

## Release 3 — separately governed capabilities

Candidates: dedicated history/config-check collectors, event subscriptions, trigger subscriptions, and future officially documented config-entry/floor/label/system interfaces. Value: potentially high. Risk: high privacy, temporal semantics, lifecycle complexity and versioning exposure. Complexity: high. HASK opportunity: temporal and lifecycle evidence only after dedicated specifications.

Connectivity, diagnostics, System Health and Repairs are not assigned to a release because the completed discovery found no documented standardized external API contract sufficient for UniFi or MikroTik connectivity. They require a new official capability or separate authoritative source, not collector inference.

## Gates

Each release requires frozen public semantics, field-level privacy review, capability fixtures from documented schemas, version-negotiation behavior, deterministic serialization and explicit consumer acceptance. This document authorizes none of those implementations.
