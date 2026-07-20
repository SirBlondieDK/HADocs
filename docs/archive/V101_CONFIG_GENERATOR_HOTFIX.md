# v1.0.1 Config + Generator hotfix

Fixes two issues found during v1.0.1 testing:

1. `CONFIG_FILE` was undefined after patching config handling.
2. `generate_index()` was called with a newer extended argument list.

## Apply

```powershell
py -3.14 tools/apply_v101_hotfix_config_generator.py
py -3.14 -m pytest
py -3.14 main.py
```

## Verify token storage

After saving Settings:

```powershell
cmdkey /list | findstr /i HADocs
findstr /i token config.json
```

Expected:

- Windows Credential Manager contains `HADocs/HomeAssistantToken`
- `config.json` does not contain token
