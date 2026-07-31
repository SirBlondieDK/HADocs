# HADocs/HASK integration status

This is the canonical current product status for the HADocs/HASK integration.
The implementation reports and governance records elsewhere under this directory
are retained as evidence, but they do not control normal product execution.

## Current product boundary

| Capability | Product status | User-visible effect |
|---|---|---|
| Normal HADocs analysis | Implemented and active | Existing findings, recommendations, reports, and Health Score are unchanged. |
| Operational SQLite database | Implemented, optional, and default-disabled | When explicitly initialized and enabled, a scan persists protected installation, scan, observation, entity, and relationship records. |
| Protected installation identity | Implemented; explicit initialization required | `hadocs database init` creates or validates one identity and protected credential. Repetition is a validated no-op. |
| HASK bundle runtime | Implemented, read-only, optional, and default-disabled | A local validated bundle can supply immutable knowledge to the candidate bridge. |
| HASK Preview | Implemented, experimental, read-only, and default-disabled | Web and generated reports show validated coverage and redacted candidate context without analytical impact. |
| HASK candidate bridge | Implemented, deterministic, read-only, and default-disabled | Candidate evidence remains separate from production analytics. |
| Native integration status | Implemented, optional, and default-disabled | Home Assistant config-entry lifecycle supplies domain-level problem evidence for the current scan. |
| UniFi and MikroTik candidates | Conservative evidence result | They remain `INSUFFICIENT_EVIDENCE` because no authenticated controller/API `connection_result` is collected. This is not an implementation failure. |
| Authenticated controller probes | Intentionally deferred | No controller connection, authentication, or network probe is performed. |
| Generic metadata collector | Deferred; runtime package excluded from the wheel | It is not part of current product execution. |

No HASK candidate changes a finding, recommendation, incident, Root Cause, or
Health Score. No raw Home Assistant entity, device, area, config-entry, or
relationship identifier is exported to HASK. Operational identities remain local,
protected, and opaque outside their owning database boundary.

## Configuration contract

Installing code does not enable any integration feature. These controls are
independent and all default to `false`:

| Configuration name | Meaning |
|---|---|
| `hask_database_enabled` | Enables operational persistence after identity initialization. |
| `hask_enabled` | Allows use of a configured, validated, read-only HASK bundle. |
| `hask_preview_enabled` | Exposes the candidate-only HASK Preview; also requires `hask_enabled`. |
| `hask_candidate_evidence_enabled` | Enables candidate-only evaluation; requires the database and HASK bundle. |
| `hask_native_integration_status_enabled` | Collects current domain-level config-entry status; requires initialized, enabled persistence. |

Operational initialization is a separate action, not an enablement side effect.
It also requires `hask_database_path` and a non-secret
`hask_database_installation_ref`. An explicit `hask_bundle_path` has strict
precedence. Windows and wheel builds otherwise discover the packaged validated
bundle. Missing or corrupt explicit configuration never silently falls back.

## HASK Preview

**Experimental preview — HASK results are candidate-only and do not affect
findings, recommendations, Root Causes or Health Score.**

The Preview distinguishes relevant HASK knowledge, a HASK candidate,
insufficient evidence, and a confirmed HADocs Root Cause. Only HADocs owns the
last category. Preview classifications are `SUPPORTED_CANDIDATE`,
`INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`, `REJECTED_CONFLICT`,
`BUNDLE_DISABLED`, `BUNDLE_UNAVAILABLE`, and `BUNDLE_INVALID`.

The product resource contains generated Consumer Contract JSON only. It is not
the HASK Knowledge Database, cannot be written at runtime, is separate from the
operational SQLite database, and is replaceable only by a later validated
release. Preview output contains no protected installation scope, entity/device
IDs, database keys, digests, credentials, addresses, URLs, or raw rows.

## Windows wheel and packaged application workflow

The `hadocs database init` and read-only `hadocs database status` commands are
available from an installed Python wheel and the packaged `HADocs.exe`. The
existing Settings dialog provides the same explicit initialization action plus
independent database, HASK, candidate-bridge, and native-status controls.

1. Install/start HADocs normally. With the fields absent or `false`, no database
   is opened and the HASK database package is not activated by a scan.
2. Use an explicit persistent configuration file and add the disabled database
   settings:

   ```powershell
   $env:HADOCS_CONFIG_FILE = "C:\HADocsData\config.json"
   ```

   ```json
   {
     "hask_database_enabled": false,
     "hask_database_path": "C:\\HADocsData\\hadocs-operational.sqlite",
     "hask_database_installation_ref": "primary-home",
     "hask_enabled": false,
     "hask_preview_enabled": false,
     "hask_candidate_evidence_enabled": false,
     "hask_native_integration_status_enabled": false
   }
   ```

   Keep the normal Home Assistant settings already created by HADocs in this
   file; the excerpt shows only integration-specific fields.
3. Initialize once while persistence remains disabled:

   ```powershell
   hadocs database init
   ```

   Repeating this command validates the existing protected identity and returns
   without rotating it. It prints no UUID, secret, or credential handle.
4. Set `hask_database_enabled` to `true`, then run a normal `hadocs generate`
   scan or use the GUI/web scan action. The shared report-generation boundary
   performs persistence before writing scan history.
5. Enable `hask_preview_enabled` and `hask_enabled` to view the packaged bundle,
   or optionally set a local `hask_bundle_path`. Enable
   `hask_candidate_evidence_enabled` only for bounded candidate evaluation. Enable
   `hask_native_integration_status_enabled` separately when current domain-status
   evidence is wanted.
6. Run the safe read-only status command. It prints only redacted configuration
   state, schema/integrity state, and aggregate counts:

   ```powershell
   hadocs database status
   ```
7. Set the four feature flags back to `false` to disable the integration. This
   does not delete the database or protected Windows credential.

## Home Assistant App workflow

The App maps persistent storage at `/config`. Its options expose initialization,
database enablement, HASK enablement, candidate evaluation, and native status as
separate controls.

1. Leave all integration booleans at their default `false` values for the first
   start. No database initialization or persistence occurs.
2. Keep `hask_database_enabled: false`, set
   `hask_database_initialize: true`, and start the App. Startup runs
   `hadocs database init` against `/config/hadocs.db`, stores protected POSIX
   credential material under `/config/.hadocs/credentials`, and retains only
   non-secret identity metadata in the App configuration area.
3. Repeated initialization validates the existing identity and does not rotate
   its secret. After successful initialization, set
   `hask_database_initialize: false`.
4. Set `hask_database_enabled: true` and start the App. A scan from the web UI
   persists to `/config/hadocs.db`; restart, rebuild, and update preserve the
   database and credential directory.
5. To use Preview, explicitly enable `hask_preview_enabled` and `hask_enabled`.
   The App's configured `/config/hask-bundle` remains an explicit external path;
   place a valid read-only consumer bundle there. Candidate
   evaluation and native integration status each require their own boolean.
6. Disabling every boolean stops initialization, persistence, and enrichment but
   does not remove the database or credential files.

The App currently has no user-facing database-status view. Successful repeat
initialization, the presence of `/config/hadocs.db` after an enabled scan, and an
offline read-only SQLite integrity/count check are the safe verification methods.
Adding a redacted status command or UI is a release usability item.

## Document navigation and classification

The classifications below cover every file under `docs/integration/` by exact
file or coherent path family. When a state JSON or review attachment belongs to
a named family, it inherits that family's classification.

| Classification | Paths/families | Current role |
|---|---|---|
| **CURRENT PRODUCT CONTRACT** | This document; `hask_runtime/{CONSUMER_MATCHER_REQUIREMENTS_INVENTORY.json,RUNTIME_CONFIGURATION.md,PRODUCTION_RUNTIME_FOUNDATION.md,BUNDLE_LIFECYCLE.md,CACHE_ARCHITECTURE.md,TRUST_FOUNDATION.md,DB-001_HASK_DATABASE_FOUNDATION.md,DB-002_EXECUTABLE_CONSTRAINT_SEMANTICS.md,ENTITY_DEVICE_RELATIONSHIPS.json}`; `hask_runtime/ca001/*` | Current runtime, schema, identity, trust, and matcher boundaries. |
| **CURRENT USER DOCUMENTATION** | The Windows and Home Assistant App workflows in this document, linked from the top-level `README.md` | Supported activation and safe verification guidance. |
| **COMPLETED IMPLEMENTATION EVIDENCE** | `hask_pilot/*`; `hask_runtime/{I-001*,IM-001*,PI1*,r004/*}`; API/discovery inventories and reports matching `API_*`, `HOME_ASSISTANT_API*`, `HOME_ASSISTANT_SIGNAL*`, `FINAL_DISCOVERY*`, `HADOCS_API_GAP_ANALYSIS.md`, `HADOCS_NATIVE_SIGNAL_INVENTORY.md`, `EVENT_MODEL_ANALYSIS.md`, `LIVE_API_RESPONSE_CATALOG.md`, `OBJECT_GRAPH_ANALYSIS.md`, `OBSERVED_STRUCTURED_SIGNALS.json`, `OFFICIAL_VS_OBSERVED_COMPARISON.md`, `PRIVACY_CLASSIFICATION_REPORT.md`, `REGISTRY_ANALYSIS.md`, and `REST_VS_WEBSOCKET_REPORT.md` | Reproducibility, discovery, validation, and completed-batch evidence. |
| **HISTORICAL GOVERNANCE/PROCESS** | `hask_runtime/{A-001*,AI-001*,AI-002*,DF-001*,DF-002*,G-001*,PS-001*,R-002*,R-003*,ARCHITECTURE_REVIEW*,ARCHITECTURAL_RISK_REGISTER.md,DESIGN_FREEZE*,OPEN_ITEMS_CLASSIFICATION.md}` | Records how earlier decisions were reached. They do not govern current normal product execution. |
| **DEFERRED DESIGN** | `hask_runtime/{GENERIC_METADATA_COLLECTOR*,PI2*,NATIVE_CONNECTIVITY*,CONFIG_ENTRY_ANALYSIS.md,CONNECTIVITY_SIGNAL_REVIEW.md,NATIVE_CONNECTIVITY_SIGNAL_SOURCE_ANALYSIS.md,UNIFI_MIKROTIK_CONNECTIVITY_DEFERRAL.md,HA_COMPANION_CONNECTIVITY_CONTRACT_ASSESSMENT.md,HASK_MATCHER_OPPORTUNITIES.md,LEGACY_MATCHER_PI2_EXECUTABILITY_REPORT.md}` | Possible future evidence sources and explicitly deferred controller/API connectivity work. |
| **OBSOLETE OR DUPLICATED CANDIDATE** | `hask_runtime/{IMPLEMENTATION_GATE.md,IMPLEMENTATION_SCOPE_BLOCKER.md}` and duplicate `*_FINAL_STATE.json`, `*_BLOCKER_STATE.json`, `*_STARTING_STATE.json`, or `*_IMPLEMENTATION_STATE.json` snapshots where the corresponding retained narrative report exists | Retained for traceability; never use these instead of this canonical status for current product decisions. |

No files are deleted or moved by this classification.

## Remaining release blockers and deferred work

- Final release-host validation still needs to exercise the packaged Windows
  Settings controls interactively; automated tests cover their explicit,
  repeat-safe initialization and independent enablement behavior.
- The App configuration and POSIX startup semantics are verified, but an actual
  Home Assistant image build/start still requires a Docker-enabled release host.
- Authenticated UniFi and MikroTik controller/API probes are deferred to a later
  version; their candidate classifications therefore remain conservative.
- HASK candidates intentionally remain outside findings, recommendations, and
  Health Score until a separately approved product contract changes that rule.
- The generic metadata collector remains deferred and excluded from packaging.
- **HASK Knowledge Coverage Expansion** is the next separately authorized product
  phase after this HADocs boundary and its user workflows are accepted. It must
  begin from the existing approximately 333-record HASK baseline and use bounded,
  reviewed Knowledge Packs in `D:\HA-Stability-Knowledge`. It must not run inside
  `C:\HomeAssistantDocs`, use private installation data, or write operational
  HADocs data back into HASK. See the [roadmap](../../ROADMAP.md#next-separate-phase-hask-knowledge-coverage-expansion).

## Recovery and release closeout checklist

- [x] Run every product and integration regression gate on the final tree.
- [x] Verify wheel contents and a clean Windows wheel installation.
- [x] Repair and verify packaged Windows imports, migration resources, and initialization/status usability.
- [x] Validate Home Assistant App configuration and shell startup syntax.
- [x] Exercise disabled, initialized, enabled, replay, restart, and disable-without-delete paths.
- [x] Verify credential permissions, redaction, and absence of raw identifiers in HASK output.
- [x] Verify the HASK bundle is read-only and its hashes remain unchanged.
- [x] Recheck schema hash, migrations, foreign keys, and integrity.
- [x] Review top-level documentation against this canonical status.
- [x] Keep historical documents in place with the classifications above.
- [x] Keep authenticated controller probes and metadata collection deferred.
- [ ] Build and start the App image on a Docker-enabled release host.
- [x] Review final Git status and confirm no generated runtime material is included.
- [ ] After the HADocs product boundary and user workflows are accepted, obtain
  separate authorization for **HASK Knowledge Coverage Expansion** in
  `D:\HA-Stability-Knowledge`; begin with the approximately 333-record coverage
  and quality baseline, then use bounded Knowledge Packs through a versioned
  read-only Consumer Contract.
- [ ] Make one eventual commit only after the product owner declares recovery finished.
