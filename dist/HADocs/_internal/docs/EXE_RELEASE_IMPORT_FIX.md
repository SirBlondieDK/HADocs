# EXE release import fix

Fixes the circular import that broke GUI imports and PyInstaller builds.

## Problem

`generator.py` imported `html_hook.py`, while `html_hook.py` imported `generator.py`.
That caused:

```text
ImportError: cannot import name 'generate_index' from partially initialized module
```

## Fix

- Remove `html_hook` import from `generator.py`
- Replace internal `generate_html_dashboard(...)` calls with `generate_index(...)`
- Keep `html_hook.py` as a lazy compatibility wrapper
- Ensure `.gitignore` does not ignore `src/hadocs/reports/*.py`

## Commands

```powershell
py -3.14 tools/fix_v1_exe_imports.py
py -3.14 -m pytest
git add -f src/hadocs/reports/generator.py src/hadocs/reports/html_hook.py .gitignore docs/EXE_RELEASE_IMPORT_FIX.md
git commit -m "Fix report imports for v1 executable build"
git push
git tag -f v1.0.0
git push origin v1.0.0 --force
```
