# Changelog

Notable changes to HADocs are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) where practical.

## [0.17.0-rc3] - 2026-08-15

### Added

- Exposed redacted HASK candidate readiness, bridge state, evaluation counts, and safe rejection diagnostics.
- Added Tuya as the third executable typed HASK matcher with deterministic `NOT_APPLICABLE`, `BLOCKED`, `NO_MATCH`, `READY`, and `REJECTED_CONFLICT` outcomes.
- Added immutable packaged HASK bundle `0.2.1` and a deterministic, validated bundle-generation workflow.

### Changed

- Distinguished matcher records from executable matchers and candidate evaluations from supported candidates.
- Included bundle `0.2.1` and its generator sources in Python, Windows, container, and source-distribution packaging paths.

### Fixed

- Applied the central disabled-entity policy at the remaining raw analyzer boundary so registry-disabled ZHA LQI entities cannot become analytical signals.

### Security and isolation

- Kept HASK experimental, local-first, read-only, redacted, and isolated from normal findings, Root Causes, recommendations, device status, and Health Score.
- Required explicit authoritative Tuya problem evidence before emitting a supported candidate.

See the [RC3 release notes](docs/release/v0.17.0-rc3.md).

## Unreleased — HASK Preview release candidate

### Added

- Added a shared immutable, redacted HASK Preview model used by web and generated HTML report surfaces.
- Added a dedicated web route, overview link, Windows setting, and Home Assistant App option; all remain default-disabled.
- Packaged the validated HASK consumer bundle `0.2.0` as a versioned, checksum-bound read-only resource.

### Changed

- Established `hadocs.version` as the documented version authority for source, wheel, CLI, GUI, frozen runtime, and HASK compatibility checks.
- Consolidated ignore rules and external temporary-test behavior for recovery-safe repository hygiene.

### Security and isolation

- Preview serialization excludes protected installation identifiers, raw entity/device IDs, database keys, credentials, addresses, and configuration URLs.
- HASK candidates remain experimental and cannot change findings, incidents, Root Causes, recommendations, severity, Health Score, Potential Health Score, or estimated gain.

## Unreleased — HADocs/HASK product consolidation

### Added

- Documented the canonical default-disabled operational database and read-only HASK product boundary.
- Added explicit Windows wheel and Home Assistant App initialization, enablement, verification, and disablement workflows.
- Added independent Home Assistant App options for repeat-safe identity initialization, operational persistence, HASK bundle use, candidate evidence, and native integration status.

### Clarified

- Protected installation, entity, and relationship persistence and restart-safe replay are implemented.
- UniFi and MikroTik remain `INSUFFICIENT_EVIDENCE` because authenticated controller/API probes are intentionally deferred.
- HASK candidate evidence does not alter findings, recommendations, Root Causes, or Health Score.
- Historical integration governance records are retained as evidence and do not control current normal product execution.

See the [canonical integration status](docs/integration/HASK_INTEGRATION_STATUS.md).

## Unreleased — HASK isolated integration pilot

### Added

- Added a disabled-by-default, read-only HASK contract loader and bounded UniFi/MikroTik evidence and candidate adapters.
- Added checksum, version, structure and reference validation plus isolated pilot fixtures, traces and reports.
- Added regression coverage for failure modes and candidate-only semantics without changing normal scans or Health Score.

## Unreleased — HASK runtime integration foundation

### Added

- Added disabled-by-default local bundle discovery, lifecycle management and internal runtime diagnostics.
- Added immutable process-local caching with checksum-based invalidation.
- Added contract, HADocs-version, manifest, typed structure, checksum and reference validation with a future signature-verifier interface.
- Added graceful startup/reload/shutdown behavior without connecting HASK to normal scans.

## [0.13.0] - Smart Home Intelligence Dashboard

### Added

- Dashboard Engine v2 and Executive Dashboard.
- Health Score v2 with score breakdowns and installation-size normalization.
- Root Cause cards and an Explain This-ready layout.
- Installation Overview, historical comparison, and generated output shortcuts.
- Windows Credential Manager support for Home Assistant tokens.
- Local, token-safe configuration behavior.
- Project roadmap, contributing guide, issue templates, and GitHub Actions tests.

### Changed

- Improved Dashboard, Root Cause Analysis, Smart Recommendations, Explorer links, and Markdown output.
- Improved Health Score explainability and disabled-entity handling.
- Improved Knowledge Pack output, scan flow, automatic Dashboard opening, Windows packaging, and project presentation.

### Fixed

- Prevented tokens from being stored in `config.json`.
- Read tokens from Windows Credential Manager at scan time.
- Preserved `output/index.html`, `output/explorer/index.html`, and `output/index.md` generation.
- Corrected report wrapper, generator compatibility, and secure GUI scan validation issues.

[0.17.0-rc3]: https://github.com/SirBlondieDK/HADocs/compare/v0.17.0-rc2...v0.17.0-rc3
[0.13.0]: https://github.com/SirBlondieDK/HADocs/releases/tag/v0.13.0
