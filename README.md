# HADocs

**Home Assistant Documentation & Analysis**

HADocs is an open-source, read-only tool that documents, analyzes, and helps maintain Home Assistant installations.

HADocs builds a core model of your Home Assistant environment, separating areas, physical devices, virtual/service devices, system devices, entities, integrations, and health signals.

## Requirements

- Python 3.11 or newer
- Home Assistant Long-Lived Access Token

## Quick start

```bash
py -3.14 -m pip install -r requirements.txt
py -3.14 main.py
```

CLI:

```bash
py -3.14 -m src.hadocs.cli.main init
py -3.14 -m src.hadocs.cli.main doctor
py -3.14 -m src.hadocs.cli.main generate
```

## Safety

HADocs is read-only by design.

It does not modify Home Assistant, call services, change entities, edit automations, or send commands to devices.

## New in v0.4.0

- Rules Engine
- Integration-aware entity classification
- Built-in rules for Ring, Tapo, Frigate, WLED, Mobile App, Spotify, Deco, Proxmox, Zigbee2MQTT, MQTT and Google
- Smarter Health Score
- Integration Health report
- Rule Match report
- Fewer false warnings from diagnostic entities
