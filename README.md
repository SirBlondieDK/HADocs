<p align="center">
  <img src="assets/banner/hero.svg" alt="HADocs - Home Assistant Analysis Platform" width="100%">
</p>

<h1 align="center">🏠 HADocs</h1>

<p align="center">
  <strong>Home Assistant Analysis Platform</strong><br>
  <em>Find root causes. Prioritize improvements. Understand your installation.</em>
</p>

<p align="center">
  <img alt="Release" src="https://img.shields.io/github/v/release/SirBlondieDK/HADocs">
  <img alt="Downloads" src="https://img.shields.io/github/downloads/SirBlondieDK/HADocs/total">
  <img alt="Stars" src="https://img.shields.io/github/stars/SirBlondieDK/HADocs">
  <img alt="License" src="https://img.shields.io/github/license/SirBlondieDK/HADocs">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue">
  <img alt="Home Assistant" src="https://img.shields.io/badge/Home%20Assistant-Compatible-41BDF5">
  <img alt="Privacy" src="https://img.shields.io/badge/Cloud-No-success">
</p>

---

## Understand your Home Assistant installation

Home Assistant installations grow over time. Devices are replaced, integrations change, entities become unavailable, and a single underlying problem can surface as hundreds of separate warnings. Raw diagnostics expose the symptoms, but rarely explain where to begin.

**HADocs** is a local-first **Home Assistant Analysis Platform** that turns installation data into a clear, evidence-based view of system health. It identifies related symptoms, groups them into likely root causes, measures their impact, and recommends the improvements that matter most.

The result is a practical answer to three questions:

- **What is happening?** An Executive Summary and intelligent Explorer make the installation understandable.
- **Why is it happening?** Root Cause Analysis connects related incidents and their evidence.
- **What should I fix first?** Health Scores, estimated repair effort, and Smart Recommendations establish priority.

> [!IMPORTANT]
> HADocs runs on your infrastructure. There is no cloud service, no telemetry, no automatic upload, and no external AI calls.

## Why HADocs?

| Typical diagnostics | HADocs |
|---|---|
| List every unavailable entity separately | Groups related symptoms into root causes |
| Present raw technical state | Produces an actionable Executive Summary |
| Leave troubleshooting order to the user | Prioritizes work by impact and estimated effort |
| Show current problems without context | Explains Health Score impact and potential improvement |
| Scatter information across multiple views | Connects Dashboard, Explorer, evidence, and exports |
| Make safe sharing difficult | Creates an optional, local, redacted Knowledge Pack |

## Core capabilities

- **Dashboard Engine** — the primary product experience for understanding health, impact, priorities, and progress.
- **Root Cause Analysis** — consolidates related symptoms into evidence-backed causes.
- **Health Score** — provides a transparent, normalized measure of current installation health.
- **Potential Health Score** — shows how prioritized repairs could improve the installation.
- **Smart Recommendations** — ranks actions using impact, affected devices and entities, expected score gain, and estimated repair time.
- **Explorer** — reveals relationships across areas, devices, entities, integrations, and findings.
- **Knowledge Pack** — creates structured local context for optional, user-controlled sharing.
- **Device Overrides** — lets users refine how specific devices are interpreted.
- **HTML and Markdown exports** — produces portable reports without making exports the primary interface.
- **Local First and Privacy First** — keeps analysis and data on infrastructure you control.

## Quick start

Choose the installation method that best fits your environment.

- [Home Assistant](#home-assistant-app)
- [Docker](#docker)
- [Windows](#windows)

## Dashboard Engine v2

![Dashboard Overview](assets/screenshots/01-dashboard-overview.png)

The Dashboard Engine is the primary HADocs experience. It is not a static report or a wrapper around generated HTML; it is the working surface for assessing an installation, investigating findings, and deciding what to do next.

From one interface, you can review:

- Executive Summary
- Health Score and Potential Health Score
- Estimated repair time
- Installation Overview
- Root Cause cards and supporting evidence
- Recommended Actions
- Analysis history
- Explorer and Knowledge Pack shortcuts

The Dashboard connects high-level status with the evidence behind it, so you can move from overview to investigation without losing context.

## Root Cause Analysis

![Root Cause Analysis](assets/screenshots/04-root-cause-analysis.png)

A long list of individual errors often describes only the visible damage. Fixing those items one at a time can waste effort when they originate from the same offline device, failed integration, or configuration issue.

HADocs groups related symptoms into a smaller set of root causes. Each group connects the likely cause with its affected devices, entities, child incidents, estimated repair time, and potential Health Score gain.

```text
Mobile App devices
3 devices offline
176 affected entities
Estimated repair time: 2 minutes
Potential Health Score gain: +8
```

In this example, 176 unavailable entities are not treated as 176 independent tasks. HADocs identifies one repair path with measurable impact.

## Health Score v2

![Installation Overview](assets/screenshots/02-installation-overview.png)

The Health Score is a prioritization tool, not an arbitrary percentage. It summarizes the observed condition of the installation using explainable penalties and gives you a stable way to compare impact, choose work, and track improvement over time.

Health Score v2 considers:

- Active affected entities
- Critical issues, warnings, and maintenance findings
- Root cause complexity
- Installation size
- Disabled entities
- Potential improvement

Disabled entities are not counted as active problems. Penalties are normalized so that large installations are not disadvantaged simply because they contain more entities.

### Transparent scoring

![Score Explanation](assets/screenshots/05-health-score-history.png)

HADocs explains why points were lost and which actions can recover them. The **Potential Health Score** estimates the outcome of addressing identified root causes, making the score useful for planning rather than merely reporting current state.

## Smart Recommendations

![Top Recommendations](assets/screenshots/03-top-recommendations.png)

Smart Recommendations turn findings into an ordered repair plan. HADocs prioritizes actions by expected value instead of asking you to work through every incident.

Depending on the available evidence, a recommendation can include:

- Likely root cause
- Affected entities and devices
- Child incidents
- Estimated repair time
- Expected Health Score gain

Fix what has the greatest impact first.

## Explorer

Explorer is an analysis tool for understanding how an installation fits together. It provides an intelligent path through areas, devices, entities, integrations, findings, and their relationships—not merely a browser for generated files.

Use Explorer to follow a root cause into its affected devices, inspect entity and integration context, and move between related evidence. This makes unfamiliar or complex installations easier to investigate without flattening them into disconnected lists.

## Knowledge Pack

The Knowledge Pack is a structured, locally generated representation of the analysis. It can provide context to an AI assistant or another person, but HADocs never sends it anywhere automatically.

You remain in control:

- The Knowledge Pack is created and stored locally.
- A redacted version is available for safer sharing.
- You decide whether to share either version.
- No automatic upload or external AI call occurs.

```text
output/knowledge/
output/knowledge/redacted/
```

## Local output and exports

![Generated Output](assets/screenshots/06-generated-output.png)

Each scan creates a local analysis package:

```text
output/
├── index.html
├── index.md
├── 00_executive_dashboard.md
├── 01_root_causes.md
├── 02_incidents.md
├── explorer/
├── knowledge/
├── history/
└── csv/
```

Available output includes the interactive HTML Dashboard, HTML Explorer, Markdown documentation, Knowledge Pack, redacted Knowledge Pack, CSV exports, and history snapshots.

The generated `output/index.html` remains available as a portable export. It is not embedded as the main HADocs interface.

## Privacy and security

HADocs is designed for private, local analysis.

- ✅ Runs locally
- ✅ No telemetry
- ✅ No cloud upload
- ✅ No external AI calls
- ✅ Home Assistant token stored in Windows Credential Manager
- ✅ `config.json` does not store tokens
- ✅ Redacted Knowledge Pack available

> [!WARNING]
> Treat Home Assistant tokens, generated reports, Knowledge Packs, local overrides, and private URLs as sensitive data. Do not commit them to a public repository.

## Installation

HADocs supports three deployment options. Each uses the same analysis engine and web interface.

| Method | Best for |
|---|---|
| Home Assistant App | Running HADocs directly inside Home Assistant |
| Docker | Servers, NAS devices, virtual machines, and LXC hosts |
| Windows | A self-contained desktop installation without a separate Python runtime |

### Home Assistant App

The app (formally known as add-on) is the easiest option when HADocs should run directly inside Home Assistant.

1. Open **Settings → Apps → Repositories** in Home Assistant.
2. Add the HADocs repository:

   ```text
   https://github.com/SirBlondieDK/HADocs
   ```

3. Refresh the App Store if HADocs does not appear immediately.
4. Install **HADocs**.
5. Configure the Home Assistant URL and Long-Lived Access Token.
6. Start HADocs.
7. Open the HADocs web interface.
8. Run your first analysis from **Overview**.

The Home Assistant App currently uses `sirblondiedk/hadocs:dev`, the project's preview/development channel. Rebuild or reinstall the app after a new image is published to pull the update.

Persistent app data is stored in the mapped `/config`, `/cache`, and `/output` directories.

### Docker

> [!NOTE]
> `sirblondiedk/hadocs:dev` is currently the only public Docker channel configured by the project. It tracks preview/development builds from `main`; no `latest` channel is published yet.

Create `docker-compose.yml`:

```yaml
services:
  hadocs:
    image: sirblondiedk/hadocs:dev
    container_name: hadocs

    env_file:
      - ./docker/hadocs.env

    environment:
      HADOCS_OUTPUT_DIR: /output

    volumes:
      - ./docker/output:/output
      - ./docker/cache:/cache
      - ./docker/config:/config

    ports:
      - "8099:8099"

    entrypoint: ["python", "-m", "src.hadocs.web.app"]

    restart: unless-stopped
```

Create the persistent directories:

```bash
mkdir -p docker/output docker/cache docker/config
```

Create `docker/hadocs.env` with your runtime configuration. Do not commit private tokens.

Start HADocs:

```bash
docker compose pull
docker compose up -d
```

Open:

```text
http://SERVER-IP:8099
```

View logs:

```bash
docker compose logs -f hadocs
```

Update to the newest published image:

```bash
docker compose pull
docker compose up -d --force-recreate
```

Check status:

```bash
docker compose ps
```

The container should remain **Up**. Docker starts the HADocs web application rather than the one-shot `generate` command.

### Windows

The Windows release does not require a separate Python installation.

1. Download the latest Windows release from [GitHub Releases](https://github.com/SirBlondieDK/HADocs/releases).
2. Extract the ZIP archive.
3. Run `HADocs.exe`.
4. Enter the Home Assistant URL and Long-Lived Access Token.
5. Start the HADocs web interface or run a scan.
6. Open the local address shown by HADocs.

To run HADocs from source:

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
$env:HADOCS_OUTPUT_DIR = Join-Path (Get-Location) "output"
py -3.14 -m src.hadocs.web.app
```

## Web interface

The web interface is the primary HADocs user experience. It includes:

- Overview
- Analysis
- Interactive Root Cause evidence
- Explorer
- Device Overrides
- Scan logs
- HTML export

The **Analysis** page is the interactive view for recommendations, Root Cause evidence, and Health Score details. It reads directly from the HADocs data API, keeping the active interface connected to the current analysis rather than a generated report.

## Persistent data

HADocs uses the following paths inside containers:

```text
/config
/cache
/output
```

Recommended Docker mappings:

```text
./docker/config:/config
./docker/cache:/cache
./docker/output:/output
```

Keep `docker/hadocs.env`, tokens, generated private reports, and local override files out of public commits.

## Development

### Prerequisites

- Git
- Python 3.11 or newer; Python 3.14 is recommended and used by the current development commands
- Docker, when building or testing container images
- Access to a Home Assistant installation for end-to-end analysis

### Set up the source tree

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
$env:HADOCS_OUTPUT_DIR = Join-Path (Get-Location) "output"
py -3.14 -m src.hadocs.web.app
```

### Run the test suite

```powershell
Remove-Item Env:HADOCS_OUTPUT_DIR -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

### Start the web application

```powershell
$env:HADOCS_OUTPUT_DIR = Join-Path (Get-Location) "output"
py -3.14 -m src.hadocs.web.app
```

### Build and run a local container

```bash
docker build -t hadocs:local .
```

```bash
docker run --rm -p 8099:8099 \
  --env-file ./docker/hadocs.env \
  -e HADOCS_OUTPUT_DIR=/output \
  -v "$(pwd)/docker/output:/output" \
  -v "$(pwd)/docker/cache:/cache" \
  -v "$(pwd)/docker/config:/config" \
  --entrypoint python \
  hadocs:local \
  -m src.hadocs.web.app
```

Before submitting changes, run the complete test suite and verify that no credentials, private URLs, generated reports, or local override data are included.

## Design principles

- **Local First** — data remains on infrastructure you control.
- **Privacy First** — no telemetry, cloud upload, or external AI calls.
- **Evidence Before Assumptions** — findings are supported by collected evidence.
- **Root Causes Before Symptoms** — related incidents are treated as a system, not an error count.
- **Explainable Prioritization** — scores and recommendations show why work matters.
- **One Analysis Engine** — Home Assistant, Docker, and Windows deployments use the same core engine.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the complete roadmap.

Current priorities:

- More precise, evidence-based integration assessments
- Better navigation between root causes, devices, entities, and integrations
- Continued web interface refinement
- Stable releases for the Home Assistant App, Docker, and Windows

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), keep changes focused, and include tests where appropriate.

Before opening a pull request:

```powershell
Remove-Item Env:HADOCS_OUTPUT_DIR -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

Do not include tokens, private Home Assistant URLs, private generated reports, or local override data.

## Built for the Home Assistant community

HADocs was created by a Home Assistant user to make complex installations easier to understand, troubleshoot, and improve.

If HADocs saves you time, consider giving the project a ⭐ on GitHub.
