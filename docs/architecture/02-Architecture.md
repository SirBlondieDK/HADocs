# HADocs architecture

HADocs uses a layered architecture so the same analysis engine can support Home Assistant, Docker, Windows, and source-based workflows.

```text
Entry points and web interface
            |
            v
       Application
            |
    +-------+-------+
    |               |
 Runtime         Configuration
                    |
                    v
                Providers
                    |
                    v
                Collectors
                    |
                    v
                  Models
                    |
          +---------+---------+
          |                   |
          v                   v
       Analysis            Reports
                              |
                              v
                           Exporters
```

## Layer responsibilities

- **Entry points** select application use cases and present results. They do not contain collection, analysis, or reporting rules.
- **Application** coordinates complete workflows without depending on transport details.
- **Runtime and configuration** identify the platform and combine local settings, credential storage, environment variables, and mandatory runtime values.
- **Providers** isolate Home Assistant API and transport details.
- **Collectors** retrieve and normalize installation data through providers.
- **Models** represent installation concepts independently of transport, platform, and output format.
- **Analysis** produces deterministic, evidence-based incidents, Root Cause Analysis, Health Score, Potential Health Score, and Smart Recommendations.
- **Reports** define structured content, while exporters convert it into HTML, Markdown, CSV, Knowledge Pack, and history output.

## Dependency rules

- Entry points call application use cases.
- Collectors access Home Assistant through providers.
- Analysis consumes normalized models.
- Reports consume models and analysis results.
- Exporters control format, not analysis content.

Reports must not call Home Assistant APIs, models must not depend on user interfaces, and collectors must not apply output formatting.

## Security and compatibility

Secrets must not be written to generated output or committed configuration files. Architecture changes should preserve documented commands, configuration behavior, output paths, and platform parity where practical.

Verify affected Home Assistant, Docker, and Windows workflows before merging cross-cutting changes.

See the [coding standards](03-Coding-Standards.md) and [project principles](PROJECT_PRINCIPLES.md), or return to the [documentation home](../README.md).
