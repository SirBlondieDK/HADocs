# Security

HADocs is designed to be read-only.

## What HADocs does

- Reads Home Assistant REST API data
- Reads Home Assistant WebSocket API registry data
- Stores local cache files
- Writes Markdown and CSV reports

## What HADocs does not do

- It does not modify Home Assistant configuration
- It does not call services
- It does not change entities
- It does not create, update, or delete automations
- It does not send commands to devices
- It does not upload your data anywhere

## Sensitive files

Never commit these files:

- `config.json`
- `config.local.json`
- `.env`
- `cache/`
- `output/`

These files may contain tokens, local IP addresses, entity names, device names, or other private information.

## Recommended token

Use a dedicated Long-Lived Access Token for HADocs.

If you no longer use HADocs, revoke the token in Home Assistant.
