# Health Score v2 safe integration

Fixes the indentation issue from the first Health Score v2 patch and integrates
the scoring model safely.

## Key points

- Keeps the existing `executive` object shape.
- Adds v2 fields onto executive instead of replacing it.
- Fixes broken indentation around `generate_executive_dashboard(...)`.
- Adds Health Score v2 explanation to the dashboard when supported.

## Apply

```powershell
py -3.14 tools/apply_health_score_v2_safe_fix.py
py -3.14 -m pytest
py -3.14 main.py
```
