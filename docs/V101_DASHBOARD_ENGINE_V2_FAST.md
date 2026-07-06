# v1.0.1 Dashboard Engine v2 fast fix

Restores a working professional `output/index.html` without internal
`html_hook` wrapper calls.

## Apply

```powershell
py -3.14 tools/dashboard_engine_v2_fast.py
py -3.14 -m pytest
py -3.14 main.py
```

Then scan and verify `output/index.html`.
