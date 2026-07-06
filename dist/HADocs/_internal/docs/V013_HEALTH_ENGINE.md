# v0.13 Health Engine

This replaces the experimental Health Score v2 patch with a safer integration in
the existing core health engine.

## What it does

- Adds `HealthScoreBreakdown`.
- Adds `calculate_health_score_v2(...)`.
- Adds `apply_health_score_v2(...)`.
- Keeps the existing executive object type intact.
- Ignores disabled entities as active problems.
- Normalizes scoring for large installations.
- Adds dashboard breakdown values when Dashboard Engine v2 is present.
- Makes the old `src/hadocs/analysis/health_score_v2.py` import-safe as a
  compatibility wrapper.

## Apply

```powershell
py -3.14 tools/apply_v013_health_engine.py
py -3.14 -m pytest
py -3.14 main.py
```
