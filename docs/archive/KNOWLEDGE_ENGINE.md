# Knowledge Engine

The HADocs Knowledge Engine exports structured local data about your Home Assistant installation.

## Location

After generating reports, knowledge files are written to:

```text
output/knowledge/
```

## Files

```text
output/knowledge/
├── manifest.json
├── inventory.json
├── health.json
├── incidents.json
├── recommendations.json
├── relationships.json
├── summary.md
└── redacted/
    ├── manifest.json
    ├── inventory.json
    ├── health.json
    ├── incidents.json
    ├── recommendations.json
    ├── relationships.json
    └── summary.md
```

## Purpose

The Knowledge Engine makes HADocs usable for local dashboards, future HTML Explorer, future Relationship Engine, local scripts, debugging, privacy-safe sharing, and optional AI workflows.

## Privacy

Knowledge export is local. HADocs does not upload these files. HADocs does not call AI providers.

## Redacted export

The redacted export attempts to remove or mask tokens, IP addresses, MAC addresses, GPS/location keys, authorization values, and password-like fields.

Redaction is best effort. Always review files before sharing publicly.

## AI-compatible, not AI-connected

```text
AI-compatible: yes
AI-connected: no
```
