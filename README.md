# HADocs

**Home Assistant Documentation & Analysis**

HADocs is a read-only tool that documents, analyzes, and helps maintain Home Assistant installations.

It builds an internal model of your Home Assistant setup and separates:

- areas
- physical devices
- virtual devices
- system devices
- entities
- integrations
- diagnostic entities
- health signals
- recommendations
- relationships

## Safety first

HADocs does not modify Home Assistant.

It only reads API data and writes local reports.

Never commit:

- `config.json`
- `config.local.json`
- `.env`
- `cache/`
- `output/`
- generated archives such as `output.zip`

## Requirements

- Python 3.11+
- Home Assistant Long-Lived Access Token

## Run

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pytest
py -3.14 main.py
```

## New in v0.6.0

v0.6.0 starts the transition from report generator to Smart Home Analyzer.

New features:

- Smart dashboard-style `index.md`
- Relationship Engine v1
- Entity relationship report
- Device relationship report
- Integration relationship report
- Weekly checkup style recommendations
- Better overview of what needs attention

The Relationship Engine currently understands basic relationships:

```text
Area
  └── Device
        └── Entity
              └── Integration
```

Future versions will expand this to automations, scripts, helpers, dashboards, scenes, and voice assistants.
