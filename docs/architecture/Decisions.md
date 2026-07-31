# Decisions

Architecture decisions should simplify maintenance, preserve platform parity, and keep analysis deterministic. Record decisions that introduce lasting constraints or change dependency boundaries.

Return to the [architecture overview](02-Architecture.md) or the [documentation home](../README.md).

## ADR: Candidate-only HASK Preview and packaged bundle

- Date: 2026-07-30
- Status: accepted
- Decision: Package one validated, versioned HASK consumer bundle as an immutable read-only resource and expose it only through a shared redacted `HaskPreviewSnapshot`. Prefer a valid explicit bundle, then the packaged bundle, then a visible unavailable state. A corrupt explicit bundle never silently falls back. Keep Preview and every HASK feature default-disabled.
- Reason: Users need useful knowledge coverage and candidate context without creating a second analytical authority or exposing installation data.
- Consequence: Web, generated reports, Windows, and the Home Assistant App share candidate-only semantics. Preview cannot change findings, incidents, Root Causes, recommendations, severity, scores, gain, or device status. HASK authoritative sources remain outside this repository.

## ADR: Consolidated optional HADocs/HASK product boundary

- Date: 2026-07-27
- Status: accepted
- Decision: Keep operational SQLite persistence, native domain-status collection, read-only HASK loading, and candidate evidence independently opt-in and default-disabled. Require explicit protected-identity initialization before persistence. Preserve candidate evidence outside findings, recommendations, Root Causes, and Health Score, and export no raw Home Assistant identifiers to HASK.
- Reason: The implemented installation, scan, observation, entity, and relationship slices are restart-safe, while the frozen UniFi/MikroTik matchers still lack an authenticated controller/API `connection_result` source.
- Consequence: UniFi and MikroTik remain conservatively `INSUFFICIENT_EVIDENCE`. Authenticated controller probes are deferred, historical governance records do not control normal execution, and current activation details live in the [canonical integration status](../integration/HASK_INTEGRATION_STATUS.md).

## ADR: Isolated HASK consumer boundary

- Date: 2026-07-24
- Status: historical pilot decision; superseded for current product status by the consolidated boundary above
- Decision: Consume HASK exclusively through its local, versioned JSON bundle using a disabled-by-default loader under `src/hadocs/knowledge/hask_pilot/`. Preserve canonical evidence, candidate causes, provenance, conflicts, gaps, applicability and verification in an isolated metadata DTO rather than converting them into production `Finding` or `IncidentV2` objects.
- Reason: HADocs owns runtime evidence, confirmation, severity, priority, grouping and Health Score. Direct conversion would lose HASK semantics and could turn hypotheses into production conclusions.
- Consequence: The pilot had no normal-scan hook and no score effect. The consolidated boundary above now governs the implemented default-disabled product integration.

## ADR: Optional HASK runtime service boundary

- Date: 2026-07-24
- Status: historical PI1 decision; runtime isolation remains applicable
- Decision: Provide HASK as an explicitly instantiated, disabled-by-default runtime service composed from discovery, validation, in-memory cache, provider and lifecycle manager interfaces. Do not connect it to normal scans in PI1.
- Reason: Runtime availability and trust must be independently testable without changing diagnostic, scoring or presentation behavior.
- Consequence: Invalid or absent bundles degrade only HASK diagnostics and candidate evidence. Snapshots remain immutable and checksum-addressed; signing remains an injectable future trust concern.

## ADR: Require exact native-signal coverage before HASK matcher execution

- Date: 2026-07-24
- Status: accepted evidence rule; the earlier PI2 product-status conclusion is superseded
- Decision: Execute a HASK matcher in normal scanning only when an existing structured native signal covers every authoritative required field with identical semantics, allowing at most declared one-to-one normalization. Legacy prose, indirect symptoms, unavailable states, local thresholds, and consumer-invented correlation rules are insufficient.
- Reason: Coverage analysis found that the two typed connectivity contracts lack native connection-result inputs, while all 23 legacy exports either depend on uncollected log/events or lack a closed executable matcher contract.
- Consequence: The exact-evidence rule remains active. The broader default-disabled product integration is implemented, while UniFi and MikroTik remain `INSUFFICIENT_EVIDENCE` and authenticated controller probes are deferred.
