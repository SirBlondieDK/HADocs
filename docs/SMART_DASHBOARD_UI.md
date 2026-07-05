# Smart Dashboard UI

This update improves the HADocs desktop GUI with a more product-like dashboard.

## Added

- Logo loading from `docs/images/logo.png`.
- Logo in sidebar.
- Logo in About dialog.
- Health Score panel in desktop app.
- Top Recommendation panel.
- Quick stats for entities, devices, integrations and root causes.
- Summary refresh after scan.
- Existing scan output opens Dashboard automatically when enabled.

## Data sources

The desktop summary reads local generated files if they exist:

```text
output/knowledge/health.json
output/knowledge/inventory.json
output/knowledge/recommendations.json
output/knowledge/incidents.json
output/history/latest.json
output/history/summary.json
```

## Privacy

This only reads local generated files.
No cloud, telemetry, analytics or AI calls are added.
