# HADocs Roadmap

This roadmap describes the agreed development direction for HADocs.

It is not a general feature wish list.

## Current platform versions

| Product | Version |
|---|---:|
| HADocs Windows | 0.15.0-rc1 |
| HADocs Core | 0.3.0-alpha |
| HADocs Docker | 0.3.0-alpha |
| HADocs Home Assistant Add-on | 0.3.0-alpha |

## Foundation

Status: completed

- Runtime detection
- Runtime-aware configuration
- Application layer
- Home Assistant provider
- Modular collectors
- Windows support
- Docker support
- Home Assistant Add-on support
- Windows Credential Manager integration
- Home Assistant Supervisor authentication

## Core models

Status: next milestone

Planned models:

- Installation
- Area
- Device
- Entity
- State
- Service
- Label
- Integration
- Automation
- Script
- Scene
- Helper

Goals:

- Replace direct dictionary access with typed models.
- Normalize Home Assistant responses.
- Keep reports independent of Home Assistant JSON.
- Enable reliable analysis and export.

## Report engine

Planned work:

- Separate report content from output formatting.
- Build reusable report sections.
- Support installation overview.
- Support areas, devices, entities, services, and labels.
- Add navigation and relationships between sections.
- Preserve compatibility with the existing Markdown output during migration.

## Exporters

Planned exporters:

- Markdown
- HTML
- JSON
- PDF

Later possibilities:

- SQLite
- Machine-readable snapshot archives

## Analysis engine

All analysis must be deterministic and rule-based.

Planned checks:

- Unavailable entities
- Devices without areas
- Entities without devices
- Duplicate or inconsistent names
- Disabled automations
- Missing labels
- Orphaned registry entries
- Unused helpers
- Broken entity references
- Dead MQTT topics
- Integration health
- Snapshot comparison

## Additional providers

Possible providers:

- MQTT
- Zigbee2MQTT
- Matter
- ESPHome
- Frigate
- Proxmox
- AdGuard Home
- Music Assistant
- Nextcloud

Providers must remain optional and must not weaken the Home Assistant core workflow.

## User interfaces

Planned interfaces:

- Windows GUI
- CLI
- Docker
- Home Assistant Add-on
- Local HTML dashboard

All interfaces must call the same application layer.

## Developer experience

Planned work:

- Unit tests
- Integration tests
- Test fixtures
- GitHub Actions
- Automated Docker builds
- Add-on build validation
- Release automation
- Contributor documentation
- Architecture decision log

## Stable release

Version 1.0 requires:

- Stable shared models
- Stable configuration behaviour
- Windows support
- Linux support
- Docker support
- Home Assistant Add-on support
- Markdown and HTML output
- Rule-based analysis
- Automated tests
- Documented release process
- Migration guidance
