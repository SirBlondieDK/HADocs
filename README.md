# HADocs

**Home Assistant Documentation & Analysis**

HADocs is a read-only Smart Home Analyzer for Home Assistant.

## New in v0.8.0

v0.8.0 introduces **Root Cause Engine v1**.

Instead of treating every unavailable entity as a separate problem, HADocs groups symptoms into incidents.

Example:

```text
176 unavailable entities

Root cause

2 mobile devices offline

Affected entities

Sebastian Wall Display: 53
Sofia Wall Display: 48
```

This makes the reports more useful and helps users fix the few things that matter most.

## Safety

HADocs is read-only.

It does not call services, change entities, edit automations, modify dashboards, or send commands to devices.
