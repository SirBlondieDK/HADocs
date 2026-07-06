# Credential Manager GUI fix

This update makes token storage explicit in the Settings dialog.

## Changes

- Settings saves Home Assistant Token directly to Windows Credential Manager.
- `config.json` never stores `token` or `ha_token`.
- Runtime config injects token from Credential Manager.
- Settings shows secure storage status.
- Settings includes "Forget token".

## Manual check

After saving Settings:

```powershell
cmdkey /list | findstr /i HADocs
findstr /i token config.json
```

Expected:

- `cmdkey` finds `HADocs/HomeAssistantToken`
- `config.json` does not contain token
