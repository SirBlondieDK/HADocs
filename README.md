# HADocs

**Understand your Home Assistant.**

HADocs is a read-only **Home Assistant Documentation & Intelligence** tool.

It documents your installation, analyzes health, groups root causes, generates a local HTML dashboard, and helps you understand what to fix first — without sending your data anywhere.

> Privacy First. Documentation First. Intelligence Second. AI Optional.

---

## New user?

Start here:

👉 [`docs/BEGINNER_GUIDE.md`](docs/BEGINNER_GUIDE.md)

This guide is written for people who are not technical.

It explains:

- how to download HADocs
- how to open PowerShell
- how to install requirements
- how to create a Home Assistant token
- how to start HADocs
- how to open the report
- what the dashboard means

---

## What HADocs does

HADocs connects to Home Assistant using a Long-Lived Access Token and reads information from the Home Assistant API.

It then generates local reports such as:

- HTML dashboard
- Markdown documentation
- CSV exports
- Health Score
- Root Cause Analysis
- Incident Collapse
- Device and integration reports
- Optional local knowledge export

HADocs is designed for users with growing Home Assistant installations who want to answer questions like:

- Why did my Health Score drop?
- Which devices need attention?
- Which integrations create the most issues?
- What should I fix first?
- Which entities, devices and integrations belong together?

---

## Start here after generating a report

Open:

```text
output/index.html
```

---

## Privacy

HADocs is local-first.

By default:

- no cloud
- no telemetry
- no analytics
- no tracking
- no AI calls
- no external upload

See [`docs/PRIVACY.md`](docs/PRIVACY.md) and [`SECURITY.md`](SECURITY.md).

---

## Installation

See [`docs/INSTALL.md`](docs/INSTALL.md).

Quick Windows setup:

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pytest
py -3.14 main.py
```

---

## Documentation

- [`docs/BEGINNER_GUIDE.md`](docs/BEGINNER_GUIDE.md)
- [`docs/INSTALL.md`](docs/INSTALL.md)
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md)
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)
- [`docs/PRIVACY.md`](docs/PRIVACY.md)
- [`docs/AI.md`](docs/AI.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/FAQ.md`](docs/FAQ.md)
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md)

---

## License

See [`LICENSE`](LICENSE).
