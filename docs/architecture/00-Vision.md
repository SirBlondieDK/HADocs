# HADocs vision

HADocs is a local-first **Home Assistant Analysis Platform** that helps users understand installation health, identify root causes, and prioritize improvements without giving up control of their data.

## Product goals

- Turn complex installation data into clear, evidence-based findings.
- Group symptoms through Root Cause Analysis instead of presenting isolated error counts.
- Make Health Score and Potential Health Score transparent and actionable.
- Connect the Dashboard Engine, Smart Recommendations, Explorer, Knowledge Pack, and exports through one analysis model.
- Provide consistent behavior across Home Assistant, Docker, and Windows.
- Keep all analysis local, private, deterministic, and read-only.

## Non-goals

HADocs is not a cloud service, an autonomous repair system, or an AI assistant. It does not modify Home Assistant or upload installation data automatically.

## Engineering direction

- One shared analysis engine across supported platforms
- Thin platform entry points and user interfaces
- Transport-independent domain models
- Evidence before assumptions
- Root causes before symptoms
- Export formats separated from analysis logic
- Credentials excluded from generated output
- Testable, deterministic behavior

See the [architecture overview](02-Architecture.md), or return to the [documentation home](../README.md).
