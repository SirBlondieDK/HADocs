<p align="center">
  <img src="assets/banner/hero.svg" alt="HADocs - Smart Home Intelligence for Home Assistant" width="100%">
</p>

<h1 align="center">🏠 HADocs</h1>

<p align="center">
  <strong>Smart Home Intelligence for Home Assistant</strong><br>
  <em>Find root causes. Improve health. Generate documentation.</em>
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

## 🚀 What is HADocs?

**HADocs** is a local-first Smart Home Intelligence tool for Home Assistant.

Instead of overwhelming you with hundreds or thousands of entities, HADocs analyzes your installation, groups symptoms into **Root Causes**, calculates a transparent **Health Score**, and generates a modern intelligence dashboard.

HADocs runs locally. No cloud. No telemetry. No external AI calls.

---

## ✨ Why HADocs?

Traditional diagnostics tell you **what** is broken.

HADocs helps you understand **what to fix first**.

| Traditional tools | HADocs |
|---|---|
| Hundreds of unavailable entities | ✅ Groups symptoms into root causes |
| Raw technical data | ✅ Executive summary |
| Manual troubleshooting | ✅ Prioritized repair plan |
| Unknown impact | ✅ Health Score prediction |
| Scattered information | ✅ Dashboard, Explorer and Markdown docs |
| Hard to share safely | ✅ Local, redacted Knowledge Pack |

---

## ❤️ Dashboard Engine v2

![Dashboard Overview](assets/screenshots/01-dashboard-overview.png)

The new Dashboard Engine gives you a product-like view of your Home Assistant installation:

- Executive Summary
- Health Score
- Potential Health Score
- Estimated repair time
- Installation Overview
- Root Cause cards
- Recommended Actions
- History
- Explorer and Knowledge Pack shortcuts

---

## ❤️ Health Score v2

![Installation Overview](assets/screenshots/02-installation-overview.png)

Health Score v2 is designed to be explainable and fair for both small and large installations.

It considers active affected entities, critical issues, warnings, maintenance issues, root cause complexity, installation size, disabled entities and potential improvement.

Disabled entities are ignored as active problems, and penalties are normalized so large installations are not punished unfairly.

---

## ⚡ Smart Recommendations

![Top Recommendations](assets/screenshots/03-top-recommendations.png)

HADocs prioritizes what matters most.

For each recommendation, HADocs can show likely root cause, affected entities, affected devices, estimated repair time, expected Health Score gain and child incidents.

Don't fix everything. Fix what matters first.

---

## 🔥 Root Cause Intelligence

![Root Cause Analysis](assets/screenshots/04-root-cause-analysis.png)

HADocs focuses on causes, not symptoms.

Instead of showing 176 unavailable entities as 176 separate problems, HADocs can group them into a single Root Cause.

```text
Mobile App devices
3 devices offline
176 affected entities
Estimated repair time: 2 minutes
Potential Health Score gain: +8
```

---

## 📈 Transparent Scoring

![Score Explanation](assets/screenshots/05-health-score-history.png)

No black box.

Health Score v2 explains why points were lost and what can improve them.

---

## 📚 Generated Output

![Generated Output](assets/screenshots/06-generated-output.png)

Every scan generates a complete local intelligence package:

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

Generated formats include interactive HTML Dashboard, HTML Explorer, Markdown documentation, Knowledge Pack, redacted Knowledge Pack, CSV exports and history snapshots.

---

## 🔍 Explorer

The Explorer lets you browse generated data by areas, devices, entities, integrations and relationships.

---

## 🧠 Knowledge Pack

HADocs exports structured local knowledge that can be used with AI assistants manually.

HADocs does **not** upload it automatically.

You choose what to share.

```text
output/knowledge/
output/knowledge/redacted/
```

---

## 🔒 Privacy first

HADocs is built for local analysis.

- ✅ Runs locally
- ✅ No telemetry
- ✅ No cloud upload
- ✅ No external AI calls
- ✅ Home Assistant token stored in Windows Credential Manager
- ✅ `config.json` does not store tokens
- ✅ Redacted Knowledge Pack available

---

## 🖥️ Installation

### Windows

1. Download the latest release from GitHub Releases.
2. Extract `HADocs-v0.13.0-win64.zip`.
3. Run `HADocs.exe`.
4. Enter your Home Assistant URL and Long-Lived Access Token.
5. Click **Scan Home Assistant**.

Python is not required for the Windows release.

### From source

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
py -3.14 main.py
```

---

## 🧪 Development

Run tests:

```powershell
py -3.14 -m pytest
```

Build Windows package:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1
Compress-Archive -Path dist\HADocs\* -DestinationPath HADocs-v0.13.0-win64.zip -Force
```

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md).

Next milestones:

- v0.14: Explain This, deeper repair guidance, dependency graph
- v0.15: Automation Intelligence, Lovelace review, Zigbee health
- v1.0: stable public release, localization, installer and automatic updates

---

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## ❤️ Built for the Home Assistant community

HADocs was created by a Home Assistant user to make troubleshooting faster, clearer and more enjoyable.

If HADocs saves you time, consider giving the project a ⭐ on GitHub.
