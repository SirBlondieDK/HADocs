# HADocs

**Home Assistant Documentation & Intelligence**

HADocs is a read-only Smart Home Intelligence tool for Home Assistant.

## New in v0.10.0

v0.10.0 introduces the first **HTML Dashboard Engine**.

After generating a report, open:

```text
output/index.html
```

The HTML dashboard includes Health Score, Potential Score, Estimated Repair Time, Root Cause cards, Top Actions, Installation overview, Search/filter, Dark theme, and a screenshot-friendly layout.

Markdown reports are still generated.

## Safety

HADocs is read-only. It does not call services, change entities, edit automations, modify dashboards, or send commands to devices.
