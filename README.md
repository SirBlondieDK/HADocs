# HADocs

**Home Assistant Documentation & Analysis**

HADocs is a read-only Smart Home Analyzer for Home Assistant.

It documents your installation, analyzes health, explains what matters, and helps you understand what to fix first.

## New in v0.7.0

v0.7.0 introduces the first version of **HADocs Intelligence**.

Instead of only listing problems, HADocs now tries to answer:

- How healthy is my installation?
- What is the main cause of problems?
- What should I fix first?
- How much will it improve the Health Score?
- Did things improve since the last scan?

## Safety

HADocs is read-only.

It does not call services, change entities, edit automations, modify dashboards, or send commands to devices.

Never commit:

- `config.json`
- `.env`
- `cache/`
- `output/`
- generated archives such as `output.zip`

## Run

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pytest
py -3.14 main.py
```
