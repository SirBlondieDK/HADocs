# Changelog

All notable changes to HADocs are documented here.

## v0.11.1 - Stability & Test Environment

### Added
- Local pytest temp folder configuration.
- Test environment documentation.
- Cleanup script for local test/cache artifacts.
- Extra tests for cleanup-safe paths.

### Changed
- Pytest now uses `.pytest_tmp` inside the project instead of the operating system temp folder.
- This avoids Windows permission errors such as `PermissionError: [WinError 5] Access denied: pytest-of-USER`.
- `.pytest_tmp/` is ignored by Git.
- Release checklist now includes local temp/cache cleanup.

### Fixed
- Pytest setup errors on Windows when `AppData\\Local\\Temp\\pytest-of-USER` is locked or inaccessible.

### Security
- Cleanup script only removes known local generated folders.
- No Home Assistant data is uploaded or transmitted.

## v0.11.0 - Foundation & Privacy Release

### Added
- Full documentation foundation.
- Rewritten professional `README.md`.
- New `docs/` structure.
- New `SECURITY.md`.
- New `CONTRIBUTING.md`.
- New `docs/PROJECT_PRINCIPLES.md`.
- New `docs/PRIVACY.md`.
- New `docs/AI.md`.
- New `docs/ARCHITECTURE.md`.
- New `docs/RELEASE_CHECKLIST.md`.
- New issue templates.
- New pull request template.
- Optional local Knowledge Export foundation.
- Redacted summary export foundation.
- Privacy helper utilities.
- Project quality metadata helper.
- Tests for privacy redaction and knowledge export.
