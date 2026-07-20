# v1.0.1 Runtime token fix

Fixes the GUI scan flow after moving Home Assistant token storage to Windows Credential Manager.

## Problem

The Settings dialog saved the token, but `App.get_cfg()` removed token values from runtime config before scan.

This caused:

```text
ERROR: Token is missing.
```

even when Windows Credential Manager contained the token.

## Fix

- `App.get_cfg()` now injects token from Windows Credential Manager into the runtime config.
- `config.json` still never stores token.
- Connection summary checks Credential Manager directly.
- First-run wizard saves token to Credential Manager.
- Doctor logs whether Credential Manager contains a token.

## Test

```powershell
py -3.14 tools/apply_v101_runtime_token_fix.py
py -3.14 -m pytest
py -3.14 main.py
```

Then:

```powershell
cmdkey /list | findstr /i HADocs
findstr /i token config.json
```
