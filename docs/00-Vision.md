# HADocs Vision

HADocs is a documentation and analysis platform for Home Assistant installations.

The project exists to make complex Home Assistant environments easier to understand, document, validate, maintain, and troubleshoot.

HADocs must work from one shared codebase across:

- Windows
- Linux
- Docker
- Home Assistant Add-on

The supported platforms may have different startup methods, configuration sources, secret stores, and release cycles, but they must use the same core logic.

## Primary goals

HADocs should:

- Generate complete and readable documentation for a Home Assistant installation.
- Provide deterministic, rule-based validation and analysis.
- Make relationships between areas, devices, entities, services, and integrations understandable.
- Produce reusable output for humans and other software.
- Support local operation without requiring cloud services.
- Keep credentials and sensitive Home Assistant data protected.
- Remain modular enough to support additional providers and exporters.

## Non-goals

HADocs is not intended to become an AI assistant or chatbot.

The project may provide recommendations and diagnostics, but these must be based on explicit rules, collected data, and transparent analysis.

## Product family

HADocs is developed as one platform with several products:

- HADocs Core
- HADocs Windows
- HADocs Docker
- HADocs Home Assistant Add-on
- HADocs Linux

All products share the same core architecture.

## Design principles

1. One codebase, multiple platforms.
2. Thin user interfaces.
3. Platform-independent core models.
4. Providers hide transport and external APIs.
5. Collectors normalize external data.
6. Reports consume models, not raw Home Assistant responses.
7. Exporters control format, not content.
8. Secrets must never be written to generated reports.
9. New features must fit the architecture before implementation.
10. Behaviour must remain testable and deterministic.
