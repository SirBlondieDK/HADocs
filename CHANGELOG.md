# Changelog

## v0.5.0

### Added
- Repository cleanup guide.
- Generated-output safety checks.
- Stronger `.gitignore`.
- Better system / virtual / physical classification rules.
- More conservative Health Score.

### Changed
- Diagnostic-only devices no longer affect Health Score.
- System integrations are excluded from physical-device scoring.
- Mobile App entities are treated as diagnostic unless explicitly important.
- Duplicate name detection is less noisy.

## v0.4.0

### Added
- Rules Engine.
- Integration-aware classification.
- Rule match report.
- Integration Health report.

## v0.3.1

### Fixed
- Python 3.11+ version handling.

## v0.3.0

### Added
- HADocs Core internal model.
- Device-level Health Engine.
