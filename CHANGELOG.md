# Changelog

Notable changes to HADocs are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) where practical.

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

[0.13.0]: https://github.com/SirBlondieDK/HADocs/releases/tag/v0.13.0
