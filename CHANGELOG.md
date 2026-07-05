# Changelog

## v0.9.0

### Added
- Incident Collapse Engine v1.
- Smart Home Intelligence Engine naming.
- Incident hierarchy: root incident with child incidents.
- Executive Dashboard now shows top collapsed incidents instead of raw incident spam.
- Hidden/child incident counting.
- Root Cause report now groups related symptoms under parent incidents.
- More conservative potential score calculation.
- Better top-action selection.

### Changed
- Integration incidents and device incidents are no longer shown as separate top-level problems when one explains the other.
- Mobile App incidents are collapsed into one parent incident with affected devices underneath.
- WLED, Frigate, MQTT and Hass.io incidents are grouped more intelligently.
- Maintenance noise is hidden from the Executive Dashboard by default.

## v0.8.0

### Added
- Root Cause Engine v1.
- Incident model.
- Incident report.
- Root cause report.
- Symptom grouping by device and integration.
