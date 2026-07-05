# HADocs

**Understand your Home Assistant.**

HADocs is a read-only **Home Assistant Documentation & Intelligence** tool.

It documents your installation, analyzes health, groups root causes, generates a local HTML dashboard, and helps you understand what to fix first — without sending your data anywhere.

> Privacy First. Documentation First. Intelligence Second. AI Optional.

---

## New in v0.12.0

v0.12.0 introduces the **Smart Home Knowledge Engine**.

HADocs now creates structured local knowledge files in:

```text
output/knowledge/
```

These files make HADocs useful for local tools, future Explorer UI, future Relationship Engine, optional AI workflows, debugging, and shareable redacted reports.

HADocs still does **not** call AI services.

AI-compatible does not mean AI-connected.

---

## New user?

Start here:

👉 [`docs/BEGINNER_GUIDE.md`](docs/BEGINNER_GUIDE.md)

---

## Start here after generating a report

Open:

```text
output/index.html
```

Structured knowledge files are written to:

```text
output/knowledge/
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

See [`docs/PRIVACY.md`](docs/PRIVACY.md), [`docs/AI.md`](docs/AI.md), and [`SECURITY.md`](SECURITY.md).

---

## Documentation

- [`docs/BEGINNER_GUIDE.md`](docs/BEGINNER_GUIDE.md)
- [`docs/KNOWLEDGE_ENGINE.md`](docs/KNOWLEDGE_ENGINE.md)
- [`docs/EXPLAIN_ENGINE.md`](docs/EXPLAIN_ENGINE.md)
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

## Run

```powershell
py -3.14 -m pytest
py -3.14 main.py
```
