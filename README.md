# HADocs

**Understand your Home Assistant.**

HADocs is a read-only **Home Assistant Documentation & Intelligence** tool.

It documents your installation, analyzes health, groups root causes, generates a local HTML dashboard, and helps you understand what to fix first — without sending your data anywhere.

> Privacy First. Documentation First. Intelligence Second. AI Optional.

---

## New in v0.11.1

v0.11.1 improves stability on Windows and makes the test environment more predictable.

Pytest now uses a local project folder:

```text
.pytest_tmp/
```

instead of Windows temp folders such as:

```text
C:\Users\<user>\AppData\Local\Temp\pytest-of-<user>
```

This avoids permission problems when Windows, antivirus, or another process locks the temp directory.

Run tests:

```powershell
py -3.14 -m pytest
```

Clean local generated files:

```powershell
py -3.14 tools_cleanup.py
```

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

---

## Start here

After generating a report, open:

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
