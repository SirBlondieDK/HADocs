# HADocs Native Signal Inventory

Normal scanning currently invokes `InstallationCollector`, builds indexes, then constructs an `InstallationModel`. It does not collect Home Assistant logs, config entries, Repairs, integration diagnostics, System Health, automation/script/scene definitions, backup inventory, or explicit verification results.

| Source | Endpoint | Structured data and stable ID | Semantics | Current use | Privacy | Determinism / persistence / exposure |
|---|---|---|---|---|---|---|
| State machine | REST `/api/states` | Entity ID, state, attributes, timestamps | Explicit current state; interpretation is contextual | Entity model, availability and health analysis | Attributes may contain identifying or integration-specific data | Response order normalized indirectly by entity processing; optional raw-cache persistence; report use varies |
| Entity registry | WS `config/entity_registry/list` | Entity ID, platform, config-entry/device/area IDs, classes, capabilities | Explicit registry metadata | Platform/domain grouping and model construction | Names and IDs; no credentials expected | Collected every scan; optionally raw-cached; model/report fields consume subsets |
| Device registry | WS `config/device_registry/list` | Device ID, config-entry references, manufacturer/model/version, identifiers | Explicit registry metadata | Device construction and classification | Identifiers, host-related connections, user names may be sensitive | Collected every scan; optionally raw-cached; subsets reported |
| Area registry | WS `config/area_registry/list` | Area ID and name | Explicit registry metadata | Area grouping | User-defined location names | Collected every scan; optionally raw-cached; reported |
| Label registry | WS `config/label_registry/list` | Label ID and metadata | Explicit registry metadata | Stored in installation model | User-defined labels | Collected every scan; optionally raw-cached |
| Core config | REST `/api/config` | Version, components and exposed Core configuration facts | Explicit installation metadata | Stored in installation model | Installation metadata; no token copied by collector | Collected every scan; optionally raw-cached |
| Services | REST `/api/services` | Domain/service definitions and schemas | Explicit service availability, not execution success | Stored in installation model | Usually low; schemas can be large | Collected every scan; optionally raw-cached |
| Entity attributes | Part of `/api/states` | Device class, unit, supported features and integration-defined attributes | Explicit values, but meanings vary by domain/integration | Naming, state context and downstream analysis | Unknown attributes cannot be assumed safe | Allowlisted only when consumed; raw cache is explicitly security-warned |
| Platform/domain identifiers | Entity registry `platform` and entity ID domain | Structured identifiers | Explicit identity only | Integration grouping | Low | Deterministic grouping; exposed through models |
| Device classes / units / supported features | State attributes and registry fields | Enumerated or numeric metadata | Explicit capability/measurement metadata | Available to analysis; not a general observation contract | Low to moderate depending on attributes | Existing scan data; no generic evidence export |
| Scanner validation/API failure | Collector exception boundary | Exception/status at scan operation level | Explicit collection failure, not integration connectivity | Existing scan behavior; failure generally propagates or is logged | Exception text may leak endpoints | No standardized native observation or report contract |
| Scanner-generated health/configuration findings | Derived from model | HADocs-specific status, scores and rules | Derived, not raw evidence | Native diagnostics and reports | Depends on source data | Deterministic rules; some persisted reports |
| Automation/script/scene configuration | Not collected | None | Not available | None | Could contain secrets and personal logic | `SOURCE_NOT_COLLECTED` |
| Config entries / manifests | Not collected by normal scan | Home Assistant can expose entry ID/domain/lifecycle | Lifecycle is explicit; connectivity is not | None | Titles/reasons/placeholders may disclose data | `SOURCE_NOT_COLLECTED`; reviewed separately in native-connectivity blocker |
| Repairs / diagnostics / System Health | Not collected | Integration-specific structured payloads | No standardized connectivity semantics | None | Diagnostics are high risk without allowlists | `SOURCE_NOT_COLLECTED` |
| Home Assistant / Supervisor logs | Not collected | Logger scope plus free message | Exact signatures could be matched, but no native log stream exists | HADocs has only its own scan log | Potential secrets and identifiers | `SOURCE_NOT_COLLECTED` |
| Explicit verification results | Not collected | None | Not available | None | Unknown | `SOURCE_NOT_COLLECTED` |

No existing native source directly provides the typed matchers' `connectivity_result`, `connection_result`, and `problem_signal` semantics.

