# HADocs Architecture

## Overview

HADocs uses a layered architecture so the same core can run on Windows, Linux, Docker, and as a Home Assistant Add-on.

```text
CLI / GUI / Docker / Home Assistant Add-on
                    |
                    v
              Application
                    |
          +---------+---------+
          |                   |
          v                   v
       Runtime              Config
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
                    +-----------+-----------+
                    |                       |
                    v                       v
                 Analysis                 Reports
                                             |
                                             v
                                          Exporters
Entry points

Entry points include:

CLI
Windows GUI
Docker command
Home Assistant Add-on startup script

Entry points must remain thin.

They may:

Parse user input.
Select an application use case.
Return an exit code.
Display results.

They must not:

Call Home Assistant directly.
Collect installation data.
Build reports.
Contain analysis rules.
Application layer

The application layer coordinates complete use cases.

Current applications:

InitApplication
DoctorApplication
GenerateApplication

Example flow:

GenerateApplication
    -> load configuration
    -> validate configuration
    -> create provider
    -> collect installation data
    -> build indexes or models
    -> generate reports
    -> return exit code

The application layer must not know REST paths, WebSocket message types, or credential-store implementation details.

Runtime layer

The runtime layer detects the execution environment.

Supported environments:

Home Assistant Add-on
Docker
Windows
Linux

Detection priority:

Home Assistant Supervisor token
Container markers combined with HADocs environment configuration
Windows platform
Linux fallback

Runtime detection must not load the complete application configuration.

Configuration layer

The configuration layer merges values using this priority:

Default values
Local configuration file
Platform secret store
HADOCS environment variables
Mandatory runtime overrides

Home Assistant Add-on runtime values are mandatory:

ha_url = http://supervisor/core
token = SUPERVISOR_TOKEN

Secrets must not be written to config files.

Security layer

The security layer handles credentials and sensitive files.

Windows tokens are stored using Windows Credential Manager.

Docker uses environment variables.

The Home Assistant Add-on uses the Supervisor token.

Generated output and raw cache must be treated as potentially sensitive.

API layer

The API layer contains low-level Home Assistant communication.

Responsibilities:

HTTP requests
WebSocket authentication
WebSocket calls
Timeouts
Transport errors

The API layer must not:

Read config files.
Detect runtime.
Build reports.
Interpret installation structure.
Provider layer

Providers hide external transport details from the rest of HADocs.

Current provider:

HomeAssistantProvider

Examples:

get_states()
get_config()
get_services()
get_entities()
get_devices()
get_areas()
get_labels()
test_connection()

Only providers should normally depend directly on API clients.

Collector layer

Collectors fetch and organize data through providers.

Current collectors:

StatesCollector
ConfigCollector
ServicesCollector
EntitiesCollector
DevicesCollector
AreasCollector
LabelsCollector
InstallationCollector

InstallationCollector acts as the collection orchestrator.

Collectors may:

Call provider methods.
Normalize provider results.
Log collection progress.
Write optional raw cache through a dedicated cache component.

Collectors must not:

Generate Markdown or HTML.
Apply presentation formatting.
Access credentials directly.
Model layer

The model layer will become HADocs' internal representation of an installation.

Planned examples:

InstallationModel
AreaModel
DeviceModel
EntityModel
StateModel
ServiceModel
LabelModel

Models must be independent of:

Home Assistant transport details
CLI
GUI
Docker
Home Assistant Supervisor
Output format
Analysis layer

The analysis layer performs deterministic rule-based checks.

Analysis consumes models and produces findings.

A finding should contain:

Rule identifier
Severity
Summary
Explanation
Related object identifiers
Optional remediation guidance

Analysis must not depend on report formatting.

Report layer

The report layer defines report structure and content.

Examples:

Overview
Areas
Devices
Entities
Services
Labels
Analysis findings

Reports consume models and analysis results.

Reports must not call providers or APIs.

Exporter layer

Exporters convert report structures into output formats.

Planned exporters:

Markdown
HTML
JSON
PDF

Exporters control syntax and presentation.

They must not collect data or apply Home Assistant-specific business logic.

Dependency rules

Allowed dependency direction:

Entry points
    -> Application
    -> Runtime and Config
    -> Providers
    -> API

Application
    -> Collectors
    -> Models
    -> Analysis
    -> Reports
    -> Exporters

Disallowed examples:

Reports -> HomeAssistantAPI
Models -> GUI
Collectors -> Markdown exporter
API -> config.json
Provider -> CLI
Compatibility strategy

Large migrations must preserve current behaviour.

During refactoring:

Existing commands must keep working.
Existing report paths should remain stable where possible.
Compatibility wrappers may be used temporarily.
Windows, Docker, and Home Assistant Add-on must be tested before merge.
