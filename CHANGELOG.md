# Changelog

## v0.12.0 - Smart Home Knowledge Engine

### Added
- Knowledge Engine v1.
- Structured local knowledge export.
- `output/knowledge/manifest.json`.
- `output/knowledge/inventory.json`.
- `output/knowledge/health.json`.
- `output/knowledge/incidents.json`.
- `output/knowledge/recommendations.json`.
- `output/knowledge/relationships.json`.
- `output/knowledge/summary.md`.
- Redacted knowledge export in `output/knowledge/redacted/`.
- Explain Engine v1.
- Beginner-friendly explanations for common root causes.
- HTML dashboard Explain sections.
- Documentation for Knowledge Engine and Explain Engine.
- Tests for knowledge export and explanations.

### Changed
- Knowledge export is now a first-class local output.
- README links to Knowledge and Explain documentation.
- AI wording clarified: AI-compatible, not AI-connected.

### Security
- Knowledge export is local only.
- Redacted export removes common sensitive values.
- No AI provider calls added.
- No cloud calls added.
- No telemetry added.

## v0.11.2 - Beginner Guide Release

### Added
- Beginner-friendly guide: `docs/BEGINNER_GUIDE.md`.
