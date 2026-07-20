# Setup Wizard and Desktop UX

This update makes the existing HADocs GUI the primary desktop experience.

## Added

- First-run setup wizard.
- Settings dialog.
- About dialog.
- Toolbar buttons:
  - Scan
  - Dashboard
  - Explorer
  - Markdown
  - Output
  - Settings
  - Doctor
  - About
- Progress status panel.
- Post-scan output buttons.
- Automatic Dashboard opening after scan.

## First run

If `config.json` does not exist, HADocs opens a setup wizard.

The wizard saves:

```text
config.json
```

## Safety

No cloud, telemetry, analytics or AI calls are added.
