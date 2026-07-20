# v1.0.1 Report engine cleanup

This removes the internal `html_hook` wrapper dependency and restores a proper
professional HTML dashboard at `output/index.html`.

## What changes

- `generator.py` calls `generate_executive_dashboard(...)` directly.
- `generate_executive_dashboard(...)` always writes `output/index.html`.
- The dashboard includes sidebar navigation, executive overview, health ring,
  installation metrics, top recommendation, root-cause cards, history, score
  explanation and generated-output links.
- `html_hook.py` remains only as an external compatibility wrapper.

## Test

```powershell
py -3.14 tools/report_engine_cleanup.py
py -3.14 -m pytest
py -3.14 main.py
```

After scan:

```powershell
dir output\index.html
```
