# v1.0.1 Restore professional HTML dashboard

This restores the professional `output/index.html` dashboard after the temporary
emergency HTML fallback.

## What it does

- Loads the known-good dashboard generator from commit `8613b14`.
- Replaces the current broken `generate_executive_dashboard(...)`.
- Removes internal `html_hook` wrapper usage from `generator.py`.
- Keeps `generate_index(...)` for Markdown output.

## Apply

```powershell
py -3.14 tools/restore_professional_dashboard.py
py -3.14 -m pytest
py -3.14 main.py
```

After scan:

```powershell
dir output\index.html
```

Expected:

- `output/index.html` exists.
- The professional dashboard design is back.
