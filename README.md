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

CLI:

```powershell
py -3.14 -m src.hadocs.cli.main doctor
py -3.14 -m src.hadocs.cli.main generate
```

## New in v0.5.0

- Safer `.gitignore`
- Generated ZIP files ignored
- Better device classification
- Better integration classification
- Smarter health scoring
- Device health no longer punishes diagnostic-only devices
- Mobile App, HACS, Cloud, Spotify, Google Cast and system integrations handled more intelligently
- Added cleanup guide
- Added generated-output warning
