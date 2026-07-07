# Issue #4 Step 2: Areas Report Presentation

Uses `display_area()` only in `generate_areas()`.

This keeps internal area IDs, filenames, slugify, model data, Health Engine, GUI, and Dashboard untouched.

## Test

```powershell
py -3.14 tools/apply_issue4_step2_areas_report.py
py -3.14 -m pytest
rmdir /s /q output
py -3.14 main.py generate
findstr /s /i "_uden_område _uden_omraade uden omraade omr├Ñde" output\04_areas\*.md
```
