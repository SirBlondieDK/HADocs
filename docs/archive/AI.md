# AI Compatibility

## AI-compatible, not AI-connected

HADocs can generate structured local files that are useful for AI assistants and local automation tools.

HADocs does not call AI providers.

By default:

```text
AI export: optional
AI calls: never
Cloud upload: never
Local only: yes
```

Optional knowledge files may be written to:

```text
output/knowledge/
```

Redacted exports should remove or mask tokens, IP addresses, MAC addresses, URLs, device tracker details and sensitive location data.

The user decides what to share.
