# History & Trends

HADocs stores a small snapshot after every scan and uses it to show how the installation changes over time.

## Private history

```text
output/.hadocs_history/
```

This folder stores timestamped scan snapshots.

## Public summary

```text
output/history/latest.json
output/history/summary.json
```

These files are intended for the dashboard, Explorer and future trend views.

## What is tracked

- Health Score
- Potential Score
- problem entities
- devices
- integrations
- root causes
- estimated repair time
- critical/warning/maintenance actions

## Why it matters

A single scan shows the current state.

History shows the story:

- What improved?
- What got worse?
- Which root causes are new?
- Which problems were resolved?
