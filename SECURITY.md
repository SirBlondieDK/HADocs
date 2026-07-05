# Security Policy

HADocs is designed to be safe for Home Assistant users.

## Security model

HADocs is:

- read-only
- local-first
- no cloud by default
- no telemetry
- no analytics
- no tracking
- no AI calls

HADocs reads Home Assistant data and writes local reports. It does not modify Home Assistant.

## HADocs never does this

HADocs never:

- uploads Home Assistant data
- sends telemetry
- sends analytics
- tracks users
- calls AI providers
- calls Home Assistant services
- changes entities
- changes automations
- changes dashboards
- sends commands to devices

## Tokens and secrets

Never commit:

```text
config.json
config.local.json
.env
cache/
output/
*.zip
```

Home Assistant Long-Lived Access Tokens should be treated like passwords.

## Reports

Reports may contain private smart home information such as room names, device names, entity names, local IP addresses and personal device names.

Do not share full reports publicly unless you have reviewed them.
