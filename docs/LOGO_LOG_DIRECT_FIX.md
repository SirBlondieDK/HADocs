# Logo + Developer Log direct fix

Run:

```powershell
py -3.14 tools/apply_logo_log_direct_fix.py
py -3.14 -m pytest
py -3.14 main.py
```

Fixes:
- robust logo search
- `find_logo_file`
- `LogWindow`
- developer log in a separate scrollable window
- inline log vertical scrollbar
