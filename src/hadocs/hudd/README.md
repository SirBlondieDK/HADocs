# HUDD module

HUDD is HADocs' internal Home Assistant device knowledge database.

## v0.2: Device Matcher

The matcher accepts identity fields from Home Assistant's device registry:

- manufacturer and brand
- model and product name
- hardware revision and region
- typed identifiers such as Zigbee model/manufacturer values

It returns:

- the best HUDD device candidate
- confidence from `0.0` to `1.0`
- level: `exact`, `probable`, `possible`, or `unknown`
- matched fields, warnings, and a human-readable reason

HUDD deliberately returns `unknown` when evidence is too weak. It does not force a match.

## Command-line test

From the project root:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
py -3.14 -m hadocs.hudd.cli match --manufacturer Aqara --model RTCGQ11LM
```

Zigbee/OEM example:

```powershell
py -3.14 -m hadocs.hudd.cli match `
  --manufacturer _TZ3210_mja6r5ix `
  --model TS0505B `
  --identifier zigbee_manufacturer=_TZ3210_mja6r5ix
```

## Layout

- `data/hudd.sqlite` — current seed database
- `schema/schema.sql` — complete SQLite schema
- `migrations/` — incremental schema migrations
- `importers/` — source importers
- `database.py` — connection handling
- `repository.py` — candidate retrieval
- `matcher.py` — identity normalization and scoring
- `service.py` — public HADocs-facing API
- `cli.py` — direct matcher/search commands

## Home Assistant scan integration (v0.3)

`core.builder.build_model()` now enriches every collected Device Registry entry with
an offline HUDD match. The result is stored in `DeviceModel.hudd`, rendered in each
`05_devices/*.md` report and exported in `csv/devices.csv`.

No network request is performed by the matcher. It reads only the bundled
`data/hudd.sqlite` database. Unknown devices remain `unknown` and are not forced
to match.
