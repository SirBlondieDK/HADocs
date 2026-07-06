# v1.0.1 Dashboard Engine v2 Polish

Polishes the restored dashboard:

- Logo from `docs/images/logo.png`/`logo.svg` embedded in HTML.
- Wider/sidebar navigation.
- Executive Summary section.
- Health score hero and status.
- Installation overview.
- Top recommendation/action list.
- Root cause cards with child incidents and affected entities foldouts.
- Score explanation.
- History.
- Output links.

## Apply

```powershell
py -3.14 tools/dashboard_engine_v2_polish.py
py -3.14 -m pytest
py -3.14 main.py
```
