# Release checklist

## Quality

- [ ] Complete test suite passes
- [ ] Dashboard Engine, Analysis, Explorer, and exports are verified
- [ ] Affected Home Assistant App, Docker, and Windows workflows are verified
- [ ] Health Score and Root Cause Analysis output is reviewed for regressions

## Documentation

- [ ] README and platform guides match current behavior
- [ ] Changelog reflects only shipped changes
- [ ] Roadmap contains future work rather than completed implementation detail
- [ ] Release notes and screenshots are current
- [ ] Links and Markdown have been checked

## Security and privacy

- [ ] No credentials, private URLs, generated reports, caches, or local overrides are included
- [ ] Knowledge Pack redaction is verified when export behavior changes
- [ ] No telemetry, cloud upload, or external AI calls were introduced unintentionally

## Publish

- [ ] Version metadata and tag agree
- [ ] Working tree is clean
- [ ] GitHub Actions succeeds
- [ ] Release notes are published
- [ ] Expected release artifacts are attached

Return to the [release process](Release-Process.md) or the [documentation home](../README.md).
