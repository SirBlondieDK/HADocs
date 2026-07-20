# Configuration

Configuration depends on the selected platform. Refer to the matching installation guide before changing runtime settings:

- [Home Assistant App](guides/installation/Home-Assistant-App.md)
- [Docker](guides/installation/Docker.md)
- [Windows](guides/installation/Windows.md)

HADocs may use the following values:

| Setting | Purpose |
|---|---|
| Home Assistant URL | Address of the Home Assistant instance |
| Long-Lived Access Token | Read access to installation data |
| Output directory | HTML, Markdown, CSV, and Knowledge Pack exports |
| Cache directory | Locally cached analysis input |
| Configuration directory | Persistent local settings and Device Overrides |

> [!IMPORTANT]
> Keep tokens out of `config.json`, source control, screenshots, logs, and shared reports. Platform-specific credential handling is described in [SECURITY.md](../SECURITY.md).

Next: run your first analysis with the [Quick Start](QUICKSTART.md), or return to the [documentation home](README.md).
