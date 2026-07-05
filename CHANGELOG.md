# Changelog

## v0.15.0 - Desktop GUI & README Refresh

### Added
- New modern desktop GUI foundation.
- Clear post-scan output section.
- Open Dashboard button.
- Open Explorer button.
- Open Markdown button.
- Open Output Folder button.
- Improved success message after scan.
- Optional auto-open dashboard checkbox.
- README 3.0 with project positioning, badges, screenshots and roadmap.
- `docs/images/README_IMAGES.md` describing required screenshots and logo files.
- Tests for desktop GUI output helpers.

### Changed
- README now presents HADocs as a local-first Smart Home Intelligence platform.
- README now highlights HTML Dashboard, Explorer, Knowledge Engine, Explain Engine and Privacy.
- GUI user flow is now designed around "Generate → Open Dashboard / Explorer".

### Security
- GUI open actions only open local generated files.
- No cloud, telemetry, tracking, analytics, or AI calls added.

## v0.14.0 - GUI UX Release

### Added
- GUI helper functions for opening generated outputs.
