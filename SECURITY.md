# Security Policy

HADocs is a local-first, read-only **Home Assistant Analysis Platform**. It reads installation data and writes local analysis output; it does not call Home Assistant services or modify entities, automations, dashboards, or devices.

## Supported versions

Security fixes are applied to the latest published release and the current `main` branch. Older releases may not receive security updates.

## Report a vulnerability

Do not disclose suspected vulnerabilities in a public issue, discussion, or pull request.

Use GitHub's private vulnerability reporting option on the repository **Security** page when available. If it is unavailable, contact the maintainer through the [GitHub profile](https://github.com/SirBlondieDK) to request a private reporting channel without including sensitive details.

Include:

- The affected version and platform
- A clear description of the issue and its impact
- Reproduction steps or a minimal proof of concept
- Any known mitigations

Allow reasonable time for investigation and remediation before public disclosure.

## Credentials and private data

Treat Home Assistant Long-Lived Access Tokens as passwords. Never commit credentials, private URLs, generated reports, Knowledge Packs, caches, or local Device Overrides.

Reports can contain room names, device and entity names, local IP addresses, and other private installation details. Review and redact exports before sharing them.

## Security model

- Local First and Privacy First operation
- No telemetry, analytics, tracking, cloud upload, or external AI calls
- Windows tokens stored in Windows Credential Manager
- Docker credentials supplied through local environment configuration
- Home Assistant App authentication supplied by its runtime environment
