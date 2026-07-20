# Health Score v2

Adds a more fair and more explainable Health Score.

## Changes

- Disabled Home Assistant entities are ignored as active problems.
- Penalties are normalized by enabled entity count.
- Severity and root-cause penalties are capped.
- Dashboard gets a **Health Score v2** explanation section.

## Apply

```powershell
py -3.14 tools/apply_health_score_v2.py
py -3.14 -m pytest
py -3.14 main.py
```
