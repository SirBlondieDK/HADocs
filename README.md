# HADocs

**Home Assistant Documentation & Analysis**

HADocs is an open-source tool that automatically documents, analyzes, and helps maintain Home Assistant installations.

Instead of simply listing entities and devices, HADocs builds a complete picture of your Home Assistant environment, helping you understand how your smart home is organized, identify potential issues, and improve long-term maintainability.

Whether you run a small installation or hundreds of devices across multiple integrations, HADocs aims to become the toolbox for understanding your Home Assistant setup.

---

## Project Principles

HADocs is built around three core principles:

### Safety first

HADocs is read-only by design.

It only reads data from Home Assistant APIs, analyzes it locally, and writes reports to your output folder. It does not modify devices, automations, integrations, entities, dashboards, or Home Assistant configuration.

### Useful over noisy

Home Assistant exposes many service-only entities, buttons, update entities, diagnostic entities, and integration internals.

HADocs tries to filter out noise so reports and Health Scores focus on issues that actually matter.

### Easy to use

HADocs should be usable without deep Python, Git, or Home Assistant internals knowledge.

The goal is a simple workflow:

```bash
hadocs init
hadocs doctor
hadocs generate
```

---

## Features

### 📖 Documentation

- Automatic documentation of your Home Assistant installation
- Room-based documentation
- Device documentation
- Integration documentation
- Markdown reports
- CSV export
- Architecture overview
- Network overview
- Server overview

### 🔍 Analysis

HADocs analyzes your installation and identifies:

- Offline devices
- Unavailable entities
- Unexpected unknown entities
- Devices without areas
- Duplicate friendly names
- Low battery devices
- Integration health
- Configuration inconsistencies

### ❤️ Health Score

Unlike simple statistics, HADocs calculates a meaningful Health Score.

The score is based on real-world impact instead of raw entity counts.

System entities such as action buttons, update entities, event entities, firmware controls, and service-only entities are ignored to avoid false warnings.

---

## New in v0.2.0

- Added command-line interface
- Added `hadocs init`
- Added `hadocs doctor`
- Added `hadocs generate`
- Added configuration validation
- Added token safety checks
- Added Git safety checks
- Added clearer first-run setup
- Added better error messages
- Added security documentation
- Improved project structure for future packaging

---

## Planned Features

### Relationship Engine

One of the main goals of HADocs is to understand how everything is connected.

Example:

```text
light.kitchen

Used by

✔ Morning Automation
✔ Night Script
✔ Adaptive Lighting
✔ Kitchen Dashboard
✔ Google Assistant
```

and the opposite:

```text
Morning Automation

Uses

✔ 8 lights
✔ 2 sensors
✔ 1 helper
✔ 3 scripts
```

This makes it possible to safely clean up old entities without breaking automations.

---

### Plugin System

Future versions will include dedicated plugins for:

- Proxmox VE
- Frigate
- Zigbee2MQTT
- AdGuard Home
- ESPHome
- WLED
- MQTT
- Tapo
- UniFi

allowing HADocs to generate documentation and health reports for the entire smart home—not just Home Assistant.

---

## Current Status

HADocs is under active development.

New features are added continuously, and feedback, bug reports, and pull requests are always welcome.
