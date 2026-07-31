# HADocs Roadmap

HADocs is a **Home Assistant Analysis Platform** focused on explainable findings, practical prioritization, and private local operation.

The roadmap describes intended direction, not a release commitment. Priorities may change as the analysis engine and supported platforms mature.

## Analysis quality

- Refine Health Score weighting and Potential Health Score estimates.
- Improve evidence-based integration assessments.
- Expand device classification and reduce false positives.
- Improve explanations, confidence, and verification guidance.

## Investigation and repair

- Strengthen Root Cause Analysis and child-incident grouping.
- Improve Smart Recommendations and repair-time estimates.
- Connect root causes, devices, entities, and integrations more clearly.
- Expand before-and-after analysis comparisons.

## Platform experience

- Continue Dashboard Engine and Explorer refinement.
- Improve Device Overrides workflows.
- Stabilize Home Assistant App, Docker, and Windows releases.
- Prepare localization-ready interfaces and exports.

## Automation analysis

- Detect broken entity references.
- Identify disabled, inactive, and conflicting automations.
- Add automation dependency analysis and cleanup guidance.

## Toward 1.0

- Stable shared models and configuration behavior.
- Reliable installation and update paths.
- Strong automated test coverage.
- Complete contributor, release, and migration documentation.

See the [documentation home](docs/README.md) for current guides and the [changelog](CHANGELOG.md) for shipped work.

## HASK integration

- Read-only HASK loading, optional operational persistence, protected installation/entity/relationship identity, restart-safe replay, domain-level native status, and deterministic candidate evidence are implemented.
- A shared HASK Preview model and web/report/Windows/App surfaces are implemented as an experimental, default-disabled, candidate-only product resource.
- The generated HASK consumer bundle is packaged as a versioned, checksum-bound read-only resource while retaining strict explicit-path precedence.
- Every integration feature remains explicitly opt-in and default-disabled.
- Candidate evidence remains separate from findings, recommendations, Root Causes, and Health Score.
- Authenticated UniFi and MikroTik controller probes are deferred; their current classification remains `INSUFFICIENT_EVIDENCE` rather than an inferred connectivity failure.
- Future release-host work includes interactive Windows and Docker/Home Assistant App image smoke verification.

See the [canonical integration status](docs/integration/HASK_INTEGRATION_STATUS.md)
for current capabilities, activation workflows, historical-document disposition,
and deferred scope.

## Next separate phase: HASK Knowledge Coverage Expansion

This phase begins only after the HADocs product boundary and user workflows are
verified and the product owner grants separate authorization. It is not part of
Product Consolidation Batch 6A.

The two databases have separate ownership and purposes:

- The HADocs operational SQLite database stores installation-specific scans,
  observations, protected entities, and protected relationships.
- The HASK Knowledge Database stores general, evidence-backed Home Assistant
  knowledge.
- HADocs consumes HASK only through the versioned, read-only Consumer Contract.
- Installation data must never be written back into HASK.
- HASK records must not be generated from private user installations.
- Knowledge expansion must be performed in `D:\HA-Stability-Knowledge`, under
  that project's own authorization and governance, not inside
  `C:\HomeAssistantDocs` or from the HomeAssistantDocs Work chat.

### Starting coverage baseline

Begin by inventorying and quality-classifying the existing approximately 333
records across:

- Home Assistant Core
- Supervisor and Home Assistant OS
- Recorder and supported database engines
- Backups and recovery
- Automations, scripts, and traces
- Repairs, Diagnostics, and System Health
- MQTT
- Zigbee and ZHA
- Zigbee2MQTT as an external community application
- Matter and Thread
- ESPHome
- DNS and network dependencies
- UniFi
- MikroTik
- Frigate
- Music Assistant
- AdGuard Home
- Nextcloud
- Jellyfin
- Proxmox VE
- Docker
- Major device manufacturers and ecosystems

### Expansion method

Expansion must use small, bounded, reviewable Knowledge Packs. Every new factual
claim must include an authoritative or clearly classified source,
applicability/version boundaries, evidence quality, deterministic relationships,
and validation against the existing schemas. Knowledge Packs must not invent log
signatures or universal thresholds.

The separately authorized phase must deliver, in order:

1. Coverage and quality baseline.
2. Duplicate and stale-record audit.
3. Prioritized knowledge-gap backlog.
4. Small domain-specific research batches.
5. Schema and Consumer Contract validation.
6. Deterministic bundle generation.
7. HADocs compatibility tests.
8. Release manifest and versioned bundle.
9. Conservative candidate-only activation before any finding or score effect.
