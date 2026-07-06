# HADocs v1.0.1 Token Security

HADocs now stores the Home Assistant Long-Lived Access Token in Windows Credential Manager instead of `config.json`.

## Why

This prevents accidental token sharing if a user zips or shares the HADocs folder.

## Behavior

- `config.json` stores non-sensitive settings.
- The Home Assistant token is stored in Windows Credential Manager.
- If `config.json` is deleted, HADocs can still read the saved token.
- If the HADocs folder is zipped and shared, the token is not included.

## Credential name

```text
HADocs/HomeAssistantToken
```

## Apply patch

```powershell
py -3.14 tools/apply_v101_windows_credentials.py
py -3.14 -m pytest
```
