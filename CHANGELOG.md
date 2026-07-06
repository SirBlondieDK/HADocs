# Changelog

## v0.13.0 - Smart Home Intelligence Dashboard

### Added

- Dashboard Engine v2.
- Health Score v2.
- Health Score breakdown.
- Installation-size normalized scoring.
- Disabled entity handling in scoring.
- Root Cause cards.
- Explain This-ready Root Cause layout.
- Executive Dashboard.
- Sidebar navigation.
- Installation Overview.
- Historical comparison section.
- Generated output shortcuts.
- Windows Credential Manager token storage.
- Local-only token-safe configuration behavior.
- README 3.0.
- Roadmap.
- Contributing guide.
- GitHub issue templates.
- GitHub Actions test workflow.

### Improved

- HTML dashboard generation.
- Root Cause presentation.
- Health Score explainability.
- Recommended Actions layout.
- Explorer links.
- Markdown report structure.
- Knowledge Pack output.
- GUI scan flow.
- Dashboard auto-open behavior.
- Windows release packaging flow.
- Project branding and GitHub presentation.

### Fixed

- Token no longer stored in `config.json`.
- Token is read from Windows Credential Manager at scan runtime.
- Dashboard generation writes `output/index.html`.
- Explorer still writes `output/explorer/index.html`.
- Markdown report still writes `output/index.md`.
- Removed internal report wrapper issues.
- Fixed generator compatibility problems.
- Fixed GUI scan validation with secure token storage.
