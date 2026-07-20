# Clean Health Engine v0.13

This fixes the broken experimental `analysis.health_score_v2` module and moves
Health Score v2 into the existing core health engine.

## Changes

- `src/hadocs/core/health.py`
  - adds `HealthScoreBreakdown`
  - adds `calculate_health_score_v2`
  - adds `apply_health_score_v2`
- `src/hadocs/analysis/health_score_v2.py`
  - becomes a safe compatibility wrapper
- `src/hadocs/reports/generator.py`
  - imports v2 scoring from `core.health`
  - applies v2 scoring before reports are generated
  - adds dashboard score breakdown when Dashboard Engine v2 is present

## Apply

```powershell
py -3.14 tools/apply_v013_health_engine_clean.py
py -3.14 -m pytest
py -3.14 main.py
```
