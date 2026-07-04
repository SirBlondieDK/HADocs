# HADocs

**Home Assistant Documentation & Analysis**

HADocs is an open-source tool that automatically documents, analyzes, and helps maintain Home Assistant installations.

Instead of simply listing entities and devices, HADocs builds a complete picture of your Home Assistant environment, helping you understand how your smart home is organized, identify potential issues, and improve long-term maintainability.


Whether you run a small installation or hundreds of devices across multiple integrations, HADocs aims to become the toolbox for understanding your Home Assistant setup.

---

# Features

## 📖 Documentation


## Features

- Automatic documentation of your Home Assistant installation
- Room-based documentation
- Device documentation
- Integration documentation
- Markdown reports
- CSV export
- Architecture overview
- Network overview
- Server overview

---

## 🔍 Analysis

HADocs analyzes your installation and identifies:

- Offline devices
- Unavailable entities
- Unexpected unknown entities
- Devices without areas
- Duplicate friendly names
- Low battery devices
- Integration health
- Configuration inconsistencies

---

## ❤️ Health Score

Unlike simple statistics, HADocs calculates a meaningful Health Score.

The score is based on real-world impact instead of raw entity counts.

For example:

- Critical services offline
- Physical devices unavailable
- Low batteries
- Missing room assignments
- Duplicate names
- Configuration issues

System entities such as buttons, firmware updates, and service actions are automatically ignored to avoid false warnings.

---

## 🏠 Smart Home Awareness

HADocs understands that not every Home Assistant entity represents a real device.

It automatically filters or ignores entities such as:

- button.*
- update.*
- event.*
- image.*
- firmware controls
- restart buttons
- snapshot buttons
- service-only entities

This results in much more accurate reports and Health Scores.

---

## Planned Features

### Relationship Engine

One of the main goals of HADocs is to understand how everything is connected.

Example:

```
light.kitchen

Used by

✔ Morning Automation
✔ Night Script
✔ Adaptive Lighting
✔ Kitchen Dashboard
✔ Google Assistant
```

and the opposite:

```
Morning Automation

Uses

✔ 8 lights
✔ 2 sensors
✔ 1 helper
✔ 3 scripts
```

This makes it possible to safely clean up old entities without breaking automations.

---

### Dashboard Analyzer

Automatically discover

- unused dashboard cards
- missing entities
- duplicated cards
- suggested dashboards
- room-specific dashboards

---

### Automation Analyzer

Discover

- unused automations
- orphaned scripts
- unused helpers
- broken entity references
- dead automations

---

### Plugin System (planned)

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

# Why HADocs?

Home Assistant provides an incredible amount of information, but once an installation grows beyond a few dozen devices it becomes increasingly difficult to answer questions like:

- What uses this entity?
- Can I safely delete this helper?
- Which automations depend on this device?
- Why is my Health Score decreasing?
- Which devices need maintenance?
- Which integrations generate the most problems?

HADocs aims to answer these questions automatically.

---

# Vision

Our goal is not simply to document Home Assistant.

Our goal is to create the ultimate analysis and documentation platform for Home Assistant and modern smart homes.

Think of it as **"documentation meets diagnostics."**

---

# Current Status

HADocs is under active development.

New features are added continuously, and feedback, bug reports, and pull requests are always welcome.

- Architecture, network, and server overviews
- Smart Home-aware Health Score

## Health Score v2

HADocs calculates health based on real-world impact instead of raw entity counts.

System entities such as action buttons, update entities, event entities, images, notifications, conversation agents, STT/TTS entities, firmware controls, restart buttons, and snapshot buttons are ignored to avoid false warnings.

## Current Status

HADocs is under active development.
