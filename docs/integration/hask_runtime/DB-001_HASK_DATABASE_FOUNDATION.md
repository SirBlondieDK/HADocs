# DB-001 HASK Database Foundation

Status: **COMPLETE**  
Authority: **DB-001**  
Implementation baseline: **DF-002**  
Active public contract: **hadocs-generic-metadata 1.0.0**

This is the sole DB-001 deliverable authorized by `governance/active/DB-001.md`.
It contains the DB-001A inventory, DB-001B bounded foundation decisions and
DB-001C observation-retention boundary. It does not define a relational schema,
activate a migration, change a contract, or authorize implementation.

## 1. Executive summary

The HASK provider repository owns authoritative knowledge YAML and generates a
read-only JSON consumer bundle. HADocs owns runtime collection, analysis and
operational state. The existing boundary does not permit HADocs to write into
HASK or the generated bundle.

DB-001B selects **SQLite** as the initial operational technology and a
**separate writable HASK operational SQLite file owned by HADocs** as the sole
operational database boundary. The initial deployment contract is one local
host, one logical writer service/process and serialized write transactions;
concurrent readers are allowed. PostgreSQL is not activated. A governed
technology reassessment is required if remote/multi-host access, multiple
independent writers, sustained lock contention, or a workload outside the
bounded assumptions becomes required.

DB-001C closes the observation-retention question with 12 exclusive taxonomy
classes and one retention policy per class. Only normalized, privacy-minimized
identity, current-projection, transition, compatibility and audit facts become
operational authority. Raw collector payloads and debug/temporary values are
not retained; derived and reconstructable values are regenerated.

DB-001D defines the canonical conceptual information model. Ten aggregate
roots own all operational persistence concepts; owned entities and value/reference
objects have exactly one owner, while lifecycle history remains a view over
immutable lifecycle events rather than a duplicate store. This model remains
logical: no columns, SQL types, foreign keys, executable schema, migration or
repository interface is defined.

DB-001E translates that model into 25 logical relations: 22 relations map the
canonical persisted entity types one-to-one and three association relations
represent evidence/subject joins without transferring ownership. The model is
minimum Third Normal Form except for four explicit current-state projections.
It defines logical keys, constraints, reference direction, conceptual index
families, migration ordering and unit-of-work boundaries without executable SQL
or implementation.

DB-001F fixes the documentation-only physical SQLite representation: 25 tables,
243 columns, 25 INTEGER primary keys, 28 alternate keys, 57 fixed foreign keys,
30 mapped logical constraints, 18 named secondary indexes and explicit runtime
PRAGMA/migration/recovery rules. No executable schema or migration artifact is
created.

DB-001G closes the database-foundation charter. It fixes the remaining abstract
secret-provider contract, repository error taxonomy, migration-authoring policy,
recovery matrix and implementation roadmap; verifies all prior layers; and finds
the foundation ready for a separately governed implementation increment. This
completion does not authorize implementation or change the active governance
pointer.

HADocs currently has two independent SQLite mechanisms:

1. a general application database with tables for policies, scan runs,
   findings, score snapshots and policy audit entries; only policies have a
   repository implementation; and
2. HUDD, a separate device-knowledge database shipped as a read-only SQLite
   artifact at runtime and populated by offline importers.

HADocs also persists configuration, device overrides, optional raw collection
cache, history snapshots and generated reports as files. The PI1 HASK bundle
cache and Generic Metadata Collector snapshot are intentionally process-local
and do not survive restart.

The accepted CA-001/AI-002 identity architecture requires durable state that no
existing store presently models: installation-scoped identity context,
protected provenance, installation-wide collision history, clone decisions,
stable relationship references, closed entity lifecycle transitions,
compatibility/migration state and audit evidence. Secret material requires a
protected secret store and must not be placed in public output or ordinary
logs. The existing Windows credential store is evidence of a security boundary,
but it is not a demonstrated cross-platform solution.

## 2. Governance scope

- `D:\HA-Stability-Knowledge\governance\ACTIVE.md` and
  `governance/manifests/governance_state.json` identify DB-001 as the sole
  active authority.
- `D:\HA-Stability-Knowledge\governance\active\DB-001.md` permits read-only
  repository inventory and requires this single document.
- CA-001 remains accepted and read-only; AI-002 is complete and read-only;
  DF-002 remains the implementation baseline.
- Production code, runtime, dependencies, executable schemas, migrations,
  repositories, tests, fixtures and contracts are outside this batch.

## 3. Repository map and ownership

| Repository / boundary | Evidence | Current ownership | Persistence role |
|---|---|---|---|
| HASK authoritative provider | `D:\HA-Stability-Knowledge\knowledge\`; `schemas/registry.yaml` | HASK | Authoritative YAML knowledge. Not runtime installation state. |
| HASK generation | `D:\HA-Stability-Knowledge\scripts\`; `dist\hadocs` | HASK build | Deterministic derived JSON bundle. Generated output is replaceable, not an operational database. |
| HADocs consumer/runtime | `C:\HomeAssistantDocs\src\hadocs` | HADocs | Collection, models, analysis, reports, runtime bundle activation and operational persistence. |
| HASK runtime boundary | `src/hadocs/knowledge/hask_runtime/models.py:16-32`; `cache.py:8-33`; `provider.py:6-24` | HADocs | Immutable in-memory validated bundle and diagnostics. No bundle mutation or disk cache. |
| Generic Metadata Collector | `src/hadocs/metadata_collector/contract.py:39-105`; `lifecycle.py:60-117` | HADocs | Immutable public snapshot model; active snapshot is currently memory-only. |
| Pilot adapter | `src/hadocs/knowledge/hask_pilot`; `tests/test_hask_pilot.py` | HADocs | Isolated consumer adapter and tests; not a persistence owner. |
| HUDD | `src/hadocs/hudd/README.md:41-60`; `hudd/database.py:19-38` | HADocs | Separate device-knowledge SQLite store, read-only in normal runtime. |

The operational database foundation therefore belongs on the HADocs side of
the consumer boundary. HASK owns knowledge and bundle production; it does not
own an installation's runtime identities, observations or lifecycle history.
This is a boundary finding, not a schema decision.

## 4. Existing persistence mechanisms

### 4.1 General HADocs SQLite database

Evidence: `src/hadocs/persistence/database.py:8-89` and
`src/hadocs/persistence/policy_repository.py:9-82`.

| Property | Verified behavior |
|---|---|
| Technology | Python standard-library `sqlite3`. |
| Location | `HADOCS_DATABASE_FILE`; otherwise beside `HADOCS_CONFIG_FILE`; otherwise `config/hadocs.db` (`database.py:53-60`). |
| Schema | Inline SQL creates `policies`, `scan_runs`, `findings`, `score_snapshots`, `policy_audit_log` (`database.py:8-50`). |
| Connection | One connection per context; row factory; foreign keys enabled; WAL; 5-second busy timeout (`database.py:62-81`). |
| Transactions | Context commits on success, rolls back on exception and closes. This is the current unit-of-work equivalent. |
| Migration | `migrate()` executes idempotent create statements and an index (`database.py:83-89`). There is no schema-version table or ordered general migration framework. |
| Implemented repository | `PolicyRepository` lists, reads, upserts and deletes policies. Scope/action are canonicalized JSON text. |
| Unimplemented access | No repositories or write call sites were found for `scan_runs`, `findings`, `score_snapshots` or `policy_audit_log`. |
| Authority | Policies are application state. The unused tables express intended application persistence but are not evidence of a completed write path. |
| Reuse potential | Database conventions and transaction wrapper may inform DB-001. Existing tables do not satisfy CA-001/AI-002 identity semantics. |

### 4.2 HUDD SQLite device-knowledge database

Evidence: `src/hadocs/hudd/database.py:9-38`,
`src/hadocs/hudd/schema/schema.sql`,
`src/hadocs/hudd/migrations/0002_device_matcher.sql`, and
`src/hadocs/hudd/README.md:41-60`.

- The default artifact is `src/hadocs/hudd/data/hudd.sqlite`; an alternate path
  can be supplied with `HUDD_DATABASE_PATH`.
- Normal repository access defaults to SQLite URI read-only mode. Foreign keys
  are enabled and rows use `sqlite3.Row`.
- Its normalized schema covers sources, categories, organizations, aliases,
  protocols, integrations, devices, identifiers and source records. Offline
  importers execute SQL and commit during database construction.
- `0002_device_matcher.sql` shows an ordered additive migration and records HUDD
  schema version `0.2` in metadata.
- HUDD is authoritative for its curated device-knowledge context, but it is not
  authoritative for a user's live installation identity or observations.
- Reusing HUDD's physical database or tables would conflate ownership and
  lifecycles. Its use of SQLite, read-only packaged data and migration files is
  relevant precedent only.

### 4.3 File-backed application state

| Mechanism | Evidence | Read/write and lifecycle | Classification / reuse |
|---|---|---|---|
| Configuration JSON | `platform/config_manager.py:56-160`; `platform/paths.py:20-67` | Loads and rewrites cleaned local configuration; survives restart. | Authoritative operator configuration. Not suitable for relational identity history. |
| Home Assistant token | `security/credential_store.py:3-15,79-147` | Windows Credential Manager, DPAPI-backed generic credential, local-machine persistence; plaintext config migration removes token. | Secret state. Demonstrates separation from normal config/database; Windows-specific. |
| Device overrides | `core/device_overrides.py:346-374` | JSON written through a temporary file and replacement; survives restart. | Authoritative operator overrides. Atomic file-replace pattern, but no relational transactions. |
| Optional raw cache | `collectors/installation.py:67,75-89` | Per-collector JSON when `save_raw_cache` is enabled; disabled by default. | Disposable/sensitive diagnostic cache; must not become identity authority. |
| History snapshots | `core/history.py:7,33-107,198-200` | Schema-versioned dated JSON plus `public/latest.json`; persists reports across restart. | Derived scan/report history. File writes have no cross-file transaction. |
| Reports/exports | `html/dashboard.py:42`; `html/explorer.py:101-109`; `knowledge/exporter.py:12-17,248-249`; CSV/report modules | Rebuilt output files. | Derived/disposable presentation artifacts. |
| HASK consumer bundle | `D:\HA-Stability-Knowledge\dist\hadocs`; HASK runtime loader | Deterministically generated, validated and read-only for HADocs. | Derived external input; never an operational write target. |

No pickle/binary application-state store, retention worker, cleanup scheduler,
SQLAlchemy, Alembic, `aiosqlite`, `psycopg`, `asyncpg`, PostgreSQL or
MySQL/MariaDB runtime dependency/configuration was found in either project's
dependency files or HADocs source. HASK contains knowledge *about* Home
Assistant Recorder databases; those records are not project database code.

### 4.4 Memory-only state

- `RuntimeCache` is explicitly process-local, immutable and keyed by aggregate
  bundle checksum (`knowledge/hask_runtime/cache.py:8-33`). Clearing or process
  termination loses it.
- `KnowledgeProvider` retains one active `RuntimeBundle` in memory
  (`knowledge/hask_runtime/provider.py:6-24`).
- `CollectorLifecycle._active_snapshot` is an immutable in-memory `Snapshot`;
  deactivation clears it (`metadata_collector/lifecycle.py:60-117`).
- `SnapshotSerializer` produces deterministic, sorted UTF-8 JSON bytes but does
  not write them (`metadata_collector/serialization.py:11-20`).

These mechanisms are restart-disposable and cannot satisfy durable identity or
historical transition requirements by themselves.

## 5. Runtime write paths

| Entry point / state | Medium and transaction | Failure/idempotency/restart | Status |
|---|---|---|---|
| Policy API | General SQLite through `PolicyRepository`; one connection transaction per call (`web/api/services.py:8-18`) | Rollback on exception; upsert is idempotent by policy ID; restart durable. | Authoritative application state. |
| Scan collection/model | `InstallationModel` in memory (`core/models.py:7-109`) | Recreated each scan; no DB transaction; lost on restart unless represented in history output. | Current derived runtime model. |
| Scan history | Dated JSON and latest JSON (`core/history.py:33-107`) | Separate writes can partially succeed; same-day filename can be replaced; restart durable. | Derived report history. |
| Raw collector responses | Optional per-key JSON (`collectors/installation.py:75-89`) | Best-effort local cache; no multi-file atomicity; restart durable when enabled. | Disposable, potentially sensitive. |
| Metadata snapshot | In-memory `Snapshot` and deterministic bytes (`metadata_collector/lifecycle.py:91-117`) | Candidate is normalized before activation; exception does not persist partial state; lost on restart. | Public-contract-shaped, currently ephemeral. |
| HASK provider activation | Immutable in-memory bundle/cache (`knowledge/hask_runtime/manager.py`, `cache.py`, `provider.py`) | Lifecycle preserves validated active snapshots on failed reload; process restart reloads bundle. | Derived runtime state. |
| Bundle/version metadata | In `RuntimeBundle` and `RuntimeDiagnostics` (`knowledge/hask_runtime/models.py:16-37`) | Not durable; recovered from validated bundle. | Derived/recomputable. |
| Reports/API responses/UI | Output files or response bytes (`html/*`; `web/app.py:528`) | Reports are rebuildable; API response is transient; no authoritative UI state store found. | Derived/disposable. |
| Configuration | Local JSON plus Windows Credential Manager (`platform/config_manager.py`; `security/credential_store.py`) | Config write survives restart; secrets are separately protected. | Authoritative operator state/secret. |

No current runtime write path persists HASK candidates, evidence enrichment,
clone classification, stable opaque references, installation identity or
AI-002 lifecycle state. The current `findings` and `scan_runs` tables are not
connected to discovered repository write paths.

Concurrency evidence is limited: SQLite WAL and a busy timeout are configured,
and the web application has a scan manager, but no repository statement fixes
the supported number of processes or concurrent database writers. This remains
an open deployment fact.

## 6. Existing domain models

| Concept / type | Evidence and principal fields | Persistence assumption / AI-002 overlap |
|---|---|---|
| Installation | `core/models.py:86-109`, `InstallationModel(areas, devices, entities, integrations, config, states, services, labels, raw)` | In-memory scan aggregate. It is not AI-002's logical-installation identity. |
| Entity | `core/models.py:8-33`, `EntityModel(entity_id, name, domain, platform, state, area_id, device_id, ... timestamps, registry, state_raw, raw)` | In-memory current HA facts. Raw IDs are unsuitable as public CA-001 references. |
| Device/area/integration | `core/models.py:36-75` | In-memory scan aggregates; overlap with public observation categories but no accepted identity lifecycle. |
| Metadata observation | `metadata_collector/contract.py:61-77`, including `observation_id`, `category`, `canonical_key`, source, time, fields, privacy, stability, relationships, scope | Immutable public snapshot object, memory-only. AI-002 corrects identity semantics without activating a new contract. |
| Relationship | `metadata_collector/contract.py:80-89`, including ID, predicate, `source_ref`, `target_ref`, source capability, time, resolution | Immutable public object, memory-only; 1.0.0 remains active while AI-002 correction is unactivated. |
| Snapshot/capability | `metadata_collector/contract.py:52-105` | Immutable collection result with explicit contract name/version; memory-only. |
| Runtime provider/bundle | `knowledge/hask_runtime/models.py:17-37` | Immutable validated knowledge input and diagnostics; recomputable, memory-only. |
| Scan | `domain/scans.py:6-23`, `ScanRun(id, status, timestamps, versions, counts, score, error)` | Table exists but no scan repository/write path was found. |
| Finding | `domain/findings.py:7-65`, typed category/severity/target plus UUID, confidence, metadata and policy fields | Table exists with only a subset of model fields; no repository/write path was found. |
| Incident/evidence | `core/incidents.py:8-37`; `core/incidents_v2.py:31-75` | Derived analysis objects. No persistence adapter found. Not the accepted AI-002 provenance/audit model. |
| Relationship graph | `core/relationships.py:6-52` | Derived entity/device/integration graph for a scan; no durable lifecycle. |
| Policy | `domain/policies.py:11-52`; `persistence/policy_repository.py` | Only fully implemented general-database aggregate. |
| HUDD identities | `hudd/models.py`; `hudd/repository.py` | Curated vendor/device matching identities, separate from installation-local CA-001 identity. |
| Lifecycle | `metadata_collector/lifecycle.py:18-24`; `knowledge/hask_runtime/manager.py:17-23` | Runtime service lifecycle only; not AI-002 entity lifecycle. |
| Version compatibility | `metadata_collector/versioning.py`; `knowledge/hask_runtime/validation.py:20-37` | Runtime negotiation; no durable compatibility-decision record. |
| Provenance/source references | Metadata `Source`, observation source fields and relationship refs in `contract.py` | Public snapshot fields, not protected clone provenance or installation-wide collision registry. |

No persisted root-cause candidate model was found. Candidate/evidence enrichment
remains architecturally separate from confirmed findings and must not be
inferred from the existing `findings` table.

## 7. Tests and fixtures

Storage-related tests discovered include:

- `tests/test_history.py` and `tests/test_history_trends.py`: history JSON and
  trend behavior.
- `tests/test_raw_cache_security.py`: optional raw-cache security behavior.
- `tests/test_credential_store.py`: credential storage and plaintext migration.
- `tests/platform/test_config_manager.py` and `test_migration.py`: local config
  and filesystem migration.
- `tests/test_hudd.py` and `test_hudd_homeassistant.py`: HUDD database/matching.
- `tests/test_hask_runtime.py`: bundle lifecycle, validation and memory cache.
- Metadata collector tests are present in the repository test suite even though
  their filenames are not persistence-specific; they validate immutable
  contract/lifecycle behavior, not durable storage.
- `tests/fixtures` contains pilot/consumer fixtures; these are test inputs, not
  operational persistence.

Factual gaps:

- no general `Database`/`PolicyRepository` test file was found by storage-name
  inventory;
- no migration-chain, corruption/recovery, restart durability or concurrent
  writer tests exist for a CA-001/AI-002 store;
- no tests cover atomic scan + observation + relationship + lifecycle commits;
- no cross-platform installation-secret storage test exists;
- no database fixture models installation-wide collision history.

No tests or fixtures were changed in DB-001A.

## 8. Deployment constraints

### Verified

- Python `>=3.11`; dependencies are `requests`, `websocket-client` and PyYAML
  (`pyproject.toml:1-10`). HASK development additionally pins PyYAML,
  `jsonschema` and pytest (`D:\HA-Stability-Knowledge\requirements.txt`).
- HADocs has no external database driver or ORM dependency.
- Container base is Python 3.11 slim. `/config`, `/output` and `/cache` are
  declared runtime locations and volumes (`Dockerfile:1,5-7,18-20`;
  `docker-compose.yml:12-15`).
- `AppPaths` creates configuration, output, cache and log directories under a
  configurable root (`platform/paths.py:20-67`).
- Windows secrets use Credential Manager with local-machine persistence
  (`security/credential_store.py:79-124`).
- HASK bundle consumption and HUDD matching are local/offline.
- SQLite is already available through the standard library and used in both
  writable application state and packaged read-only knowledge.

### Not established by repository evidence

- a supported Node runtime (the inspected runtime is Python);
- a production PostgreSQL/MySQL service;
- an official Home Assistant add-on storage contract for this project;
- the maximum process count or concurrent writer count;
- database size, retention duration or write-volume targets;
- a cross-platform protected store for CA-001 installation secrets;
- database backup/restore consistency requirements across DB, secret and
  configuration stores;
- an optional-dependency policy beyond the present lean dependency set.

These unknowns must not be converted into assumptions during technology or
schema design.

## 9. AI-002 persistence requirement map

The classifications below describe durable architectural need, not tables.
Sources are the accepted CA-001 package under `docs/integration/hask_runtime/ca001`
and the completed AI-002 specifications in `docs/integration/hask_runtime`.

| Accepted concept | Classification | Evidence and reason |
|---|---|---|
| Logical installation | MUST_PERSIST | Clone Identity Specification requires stable logical continuity across restarts/migrations; current `InstallationModel` is only a scan aggregate. |
| Installation scope | MUST_PERSIST | CA-001 normative framing uses installation scope; changing it is identity-affecting. |
| Installation-local secret | MUST_PERSIST in protected secret storage; MUST_NOT_PERSIST in public/ordinary DB output or logs | CA-001 Secret Lifecycle requires exactly 32 cryptographically secure random octets and prohibits disclosure. Existing Credential Manager demonstrates separation. |
| CA-001 collision registry | MUST_PERSIST | `CA-001_NORMATIVE_SPECIFICATION.md:107-121` requires installation-wide history, including removed identities; unavailability/corruption fails closed. |
| Clone continuity/discontinuity | MUST_PERSIST | Clone decisions determine whether installation scope, secret generation and references continue. |
| Authoritative declaration | MUST_PERSIST | It is highest-precedence clone authority and must survive the transition it governs. |
| Protected provenance | MUST_PERSIST | Clone Identity Specification makes protected lineage authoritative and integrity-protected; public export is prohibited. |
| Platform evidence | SHOULD_PERSIST | It may support a decision but must not independently determine identity; retention supports auditability. |
| Concurrency evidence | SHOULD_PERSIST | It can prove concurrent clone conditions; lack of evidence is not proof. Decision audit should retain evidence actually used. |
| Clone classification | MUST_PERSIST | `SAME_LOGICAL_INSTALLATION`, `DISTINCT_LOGICAL_INSTALLATION` or `UNKNOWN` affects activation and continuity. |
| Activation outcome | MUST_PERSIST | Fail-closed/activation decisions must remain reproducible and auditable. |
| Stable `source_ref` | MUST_PERSIST | Relationship Reference Correction defines stable, installation-scoped public relationship identity. |
| Entity current state | MUST_PERSIST | Removal Semantics defines a closed current-state machine whose next transition depends on prior valid state. |
| Entity observations | SHOULD_PERSIST | Required to audit transitions and historical evidence; raw/sensitive fields remain subject to exclusion. Not every raw response is required. |
| Relationship tuples | MUST_PERSIST | Stable relationship continuity and collision validation require current accepted tuples. |
| Relationship lifecycle/history | MUST_PERSIST | Deletion, recreation, continuity and historical retention are distinct normative transitions. |
| ACTIVE | MUST_PERSIST | Current lifecycle state. |
| NOT_OBSERVED | MUST_PERSIST | Current lifecycle state; must remain distinct from unavailable/removal. |
| UNAVAILABLE | MUST_PERSIST | Current lifecycle state; not removal. |
| REMOVED | MUST_PERSIST | Current lifecycle state retained during continued absence until positive transition evidence. |
| IDENTITY_INVALID | MUST_PERSIST | Current fail-closed identity state; distinct from removal. |
| HISTORICAL | MUST_PERSIST as retention designation | Removal Semantics explicitly makes it retention, not a sixth current state. |
| Scan/collection run | MUST_PERSIST | Complete/partial/failed collection context is required to interpret absence without inference and to group one atomic transition. |
| Architecture version | MUST_PERSIST with identity-bearing state | Version Compatibility separates architecture, contract, implementation and document versions. |
| Contract version | MUST_PERSIST with produced snapshots | `Snapshot.contract_version` is explicit; 1.0.0 remains active. |
| Database schema version | MUST_PERSIST | Required for deterministic migration; must remain independent from public contract version. |
| Implementation version | SHOULD_PERSIST with run/audit | Supports reproducibility but does not determine contract compatibility alone. |
| Compatibility decision | MUST_PERSIST with run/activation audit | Compatible, conditionally compatible, incompatible and unknown have closed outcomes and fail-closed consequences. |
| Migration state | MUST_PERSIST | Interrupted/failed migrations must not silently reinterpret identities. |
| Audit evidence for deterministic transitions | MUST_PERSIST | Required to reproduce authority, inputs, prior state, decision and outcome without exposing secrets/raw identifiers publicly. |
| Raw API responses | MUST_NOT_PERSIST by default | Existing cache is optional and sensitive; accepted architecture requires normalized authoritative fields, not blanket raw retention. |
| HASK runtime bundle/cache | MAY_PERSIST only as existing external bundle; runtime cache need not persist | Bundle is immutable/reloadable; `RuntimeCache` is deliberately process-local. |
| Generated reports/API responses/UI state | MAY_PERSIST as derived output; MUST_NOT become identity authority | Existing outputs are rebuildable projections. |

All requested identity-bearing concepts have a persistence classification. The
future model must separate current mutable projections from append-only or
immutable historical/audit evidence.

## 10. Risks and gaps

| ID | Class | Gap | Consequence |
|---|---|---|---|
| DB001-G-001 | BLOCKS_DATA_MODEL | No persisted distinction between logical installation identity and the current `InstallationModel` scan aggregate. | A model cannot safely reuse the same identity semantics. |
| DB001-G-002 | BLOCKS_DATA_MODEL | No installation-wide collision registry retaining removed/historical canonical tuples. | CA-001 fail-closed collision requirement cannot be met. |
| DB001-G-003 | BLOCKS_DATA_MODEL | No closed persisted entity/relationship lifecycle or separation of current state from historical retention. | AI-002 transitions cannot be deterministic across restarts. |
| DB001-G-004 | BLOCKS_DATA_MODEL | Scan completeness and evidence authority are not modeled with lifecycle transitions. | Absence could be misclassified as removal. |
| DB001-G-005 | BLOCKS_TECHNOLOGY_DECISION | Supported process/writer concurrency and expected data volume are undocumented. | SQLite/PostgreSQL concurrency fit cannot be finalized solely from current evidence. |
| DB001-G-006 | BLOCKS_TECHNOLOGY_DECISION | Backup/restore must coordinate database identity state with installation secret and protected provenance, but no cross-store policy exists. | An inconsistent restore could change identities or force fail-closed operation. |
| DB001-G-007 | BLOCKS_IMPLEMENTATION | Existing general SQLite migration is create-if-missing only and unversioned. | Durable identity migrations need ordered, transactional schema governance. |
| DB001-G-008 | BLOCKS_IMPLEMENTATION | Cross-platform secret storage is absent; current credential store is Windows-only. | Container deployment cannot yet satisfy secret lifecycle requirements. |
| DB001-G-009 | BLOCKS_IMPLEMENTATION | General DB tables except policies have no repositories/write path. | Existing names do not provide usable persistence services. |
| DB001-G-010 | BLOCKS_IMPLEMENTATION | No atomic boundary spans run, observations, relationships, collision entries, lifecycle projections and audit evidence. | Partial commits could create invalid identity state. |
| DB001-G-011 | NON_BLOCKING | HUDD has a separate schema/version lifecycle. | Keep it isolated; reuse conventions, not tables/database ownership. |
| DB001-G-012 | NON_BLOCKING | History JSON duplicates derived scan presentation. | It may remain a projection or later consume DB state; no migration is required for foundation design. |
| DB001-G-013 | IMPLEMENTATION_DETAIL | Exact indexes, batching, retention windows and vacuum/checkpoint policy are undefined. | Resolve after canonical keys and workload are specified. |
| DB001-G-014 | IMPLEMENTATION_DETAIL | Existing raw cache cleanup/retention is not formalized. | It must remain outside identity authority regardless of later cleanup policy. |

No accepted CA-001, AI-002 or DF-002 conflict was found. The gaps require
database foundation design; they do not require reopening identity architecture.

## 11. Candidate technology evidence (no selection)

| Candidate | Evidence for | Evidence against / unknown | Current assessment |
|---|---|---|---|
| SQLite | Already used twice; standard library; general DB has FK/WAL/rollback; single local file fits Windows and mounted `/config`; offline; low dependency footprint; easy temporary test DB. | Writer/process ceiling and workload are unknown; existing migration scheme is insufficient; DB+secret consistent backup needs design; WAL sidecars affect backup operations. | Viable repository-standard candidate. No final selection in DB-001A. |
| PostgreSQL | Strong transactional relational engine and multi-writer support in principle. | No driver, ORM, service, URL/config, Docker service, tests or deployment evidence exists in HADocs; adds service/network/backup/credential operations and dependency footprint. | Technically possible but not repository-supported by current evidence. |
| Existing HUDD SQLite artifact | Shows normalized schema, migration file and offline/read-only distribution pattern. | Different ownership, authority and lifecycle; packaged read-only data cannot hold installation state. | Useful precedent, not a shared operational store. |
| JSON/filesystem state | Already used for config, overrides, history and derived outputs; portable and inspectable. | No relational constraints, installation-wide uniqueness, multi-record atomicity or migration framework. | Suitable for existing projections/configuration, not demonstrated as a canonical relational identity store. |

MySQL/MariaDB, SQLAlchemy, Alembic and asynchronous database drivers have no
runtime repository support. They are not evidence-backed initial candidates at
this stage.

## 12. DB-001A open factual questions

1. What deployment modes are normative for the future identity store: Windows
   desktop only, Docker, an HA add-on, or all three?
2. Can more than one HADocs process write the same installation database, and
   what is the maximum expected concurrent writer count?
3. What are expected installation sizes, scan frequency, observation volume and
   historical retention duration?
4. Which protected secret facility is available in non-Windows deployments?
5. What is the required atomic backup/restore unit across database, secret,
   protected provenance and configuration?
6. Does DB-001 retain every normalized observation or only those necessary for
   current state, transition audit and configured history?
7. Are existing history JSON files retained solely as reports, or is a later
   one-time import expected? No import authority exists now.
8. Will the existing general application DB host the new bounded context, or
   will HADocs use a separate operational database file? This is a design choice
   for the next batch, not an inventory fact.

## 13. Inputs required by the next DB-001 batch

The next batch should resolve the canonical persistence-boundary and technology
decision using:

- this verified inventory;
- CA-001 collision, secret, migration and recovery rules;
- AI-002 clone, relationship, removal and compatibility specifications;
- explicit deployment/concurrency/backup assumptions, each labeled if not yet
  repository-verified;
- the existing general SQLite transaction conventions and HUDD migration
  precedent; and
- a strict separation between protected secret storage, current projections,
  immutable history/audit and generated public output.

This was the DB-001A recommendation. DB-001B below consumes it and supersedes
the next-batch instruction without altering the inventory evidence.

## 14. Traceability

| Inventory conclusion | Repository/architecture evidence |
|---|---|
| HASK is read-only knowledge input to HADocs | DB-001 authority; `dist/hadocs`; HASK runtime bundle models/loader |
| Operational identity belongs to HADocs boundary | `core/models.py`; metadata collector; HASK runtime; absence of HASK runtime writes |
| Stable opaque references require durable secret/scoping/collision state | CA-001 Normative Specification, Secret Lifecycle, Migration and Recovery |
| Clone state requires authority/provenance and ambiguity gates | `AI-002_CLONE_IDENTITY_SPECIFICATION.md` |
| Relationships require stable `source_ref` lifecycle | `AI-002_RELATIONSHIP_REFERENCE_CORRECTION.md` |
| Current lifecycle and HISTORICAL retention are distinct | `AI-002_REMOVAL_SEMANTICS.md` and its consistency correction/re-review |
| Version dimensions are independent | `AI-002_VERSION_COMPATIBILITY.md` |
| Public contract remains 1.0.0 | `metadata_collector/contract.py:9-11`; DB-001 authority; DF-002 |
| Existing relational precedent is SQLite | `persistence/database.py`; `hudd/database.py`; HUDD SQL/migration |

## 15. DB-001A validation

| Check | Result |
|---|---|
| DB-001 remained sole active authority | PASS |
| Governance transition performed | NO |
| HASK and HADocs inspected | PASS |
| Authoritative, derived and disposable storage distinguished | PASS |
| Every requested AI-002 identity concept classified | PASS |
| Final database technology selected | NO |
| Production/runtime code changed | 0 |
| Dependencies/configuration changed | 0 |
| Executable schemas/migrations created | 0 |
| Tests/fixtures changed | 0 |
| Contract changed or activated | 0 |
| CA-001/AI-002/DF-002 modified | 0 |
| Implementation started | NO |

DB-001A remains complete. The DB-001B decisions and validation follow.

## 16. DB-001B decision summary

| ID | Decision | Evidence and rationale | Consequence | Revisit trigger |
|---|---|---|---|---|
| DB001-D-001 | HADocs owns installation-local operational persistence; HASK YAML/bundle and HUDD remain read-only external knowledge. | DB-001A repository boundary and existing consumer architecture. | Operational writes never target HASK or HUDD. | A later governed consumer-boundary change. |
| DB001-D-002 | Use one separate writable HASK operational database file, not the existing general HADocs database. | Identity state has distinct fail-closed, backup, migration and retention semantics; existing general tables are incomplete and policy-oriented. | Failure/migration isolation and testability improve; configuration must eventually identify one local file. | Product governance deliberately unifies bounded contexts after compatibility proof. |
| DB001-D-003 | Initial database technology is SQLite. | Standard-library availability, two repository precedents, offline/local deployment, WAL precedent and no external-driver/service support. | No new database service or driver; schema/migrations remain future work. | Escalation gate in section 18. |
| DB001-D-004 | Initial writer model is one logical writer service/process per database; threads may submit work only through that serialized owner. | Existing local deployment and SQLite transaction precedent; multi-writer requirements are unproven. | Independent multi-process and remote writers are unsupported initially. | Required multi-process writers, remote/multi-host use or sustained contention. |
| DB001-D-005 | Secret material belongs to an external protected secret-store boundary; the DB retains only a non-secret stable handle and validation metadata. | CA-001 secret lifecycle and existing Windows Credential Manager separation. | Missing/mismatched secrets fail closed; Linux/container provider is required before implementation. | New governed secret architecture. |
| DB001-D-006 | The consistent recovery unit is operational DB + matching secret + protected provenance + identity-relevant operator configuration. | CA-001 recovery and AI-002 clone continuity. | Reports, caches, HUDD and HASK bundle are not part of the atomic identity unit. | A later architecture proves safe independent recovery. |
| DB001-D-007 | Structural invariants use DB constraints; transition/authority rules use a transaction service; secrets use the secret boundary; migrations validate both. | Prevents an application-only enforcement model while respecting rules that SQL structure cannot decide. | Every invariant has a primary layer and fail behavior in section 21. | Schema review finds a rule cannot be enforced by its assigned layer. |
| DB001-D-008 | Schema versions use an independent ordered integer sequence stored inside the operational DB; startup and migrations fail closed on unsupported state. | Existing HUDD migration precedent and AI-002 version separation. | Contract 1.0.0 remains unchanged and independent. | A future governed migration framework supersedes this convention. |

## 17. Persistence ownership and operational database boundary

The canonical boundaries are:

- **HASK provider:** authoritative YAML and generated consumer bundle; read-only
  to HADocs and never operational identity authority.
- **HUDD:** separate packaged/read-only device-knowledge SQLite database; never
  installation identity authority.
- **HADocs general database:** existing policies and any separately governed
  general scan features; it does not host the DB-001 bounded context.
- **HASK operational database:** one separate writable SQLite file owned by
  HADocs. It owns installation context, non-secret secret reference metadata,
  collision history, current projections, normalized retained observations,
  relationships, scan/run state, compatibility/migration state and audit.
- **Protected secret provider:** owns the CA-001 secret bytes outside SQLite.
- **Generated reports and caches:** derived projections, never authority.

### Boundary evaluation

| Criterion | Existing general HADocs DB | Selected separate HASK operational DB |
|---|---|---|
| Ownership | Mixes policy/general state with identity context. | Explicit HADocs-owned HASK operational bounded context. |
| Backup/restore | Fewer files, but unrelated policy restore becomes coupled to identity recovery. | Identity recovery unit is explicit and can be validated with its secret/provenance. |
| Migration isolation | Existing unversioned create-only migration increases coupling. | Independent ordered schema lifecycle can fail closed without blocking unrelated policy schema decisions. |
| Failure isolation | Corruption/locks affect general policies and identity together. | Identity failure deactivates this capability without redefining unrelated general state. |
| Lifecycle/retention | Existing tables do not encode CA-001/AI-002 retention. | Purpose-built retention without altering policy ownership. |
| Testability | Requires filtering unrelated general state. | Empty temporary file represents the whole bounded context. |
| Deployment | One extra local file. | Still local/offline and no extra service. |
| Future PostgreSQL migration | Entangled table ownership. | Repository boundary can later receive another adapter after governance. |

The selected separation is logical and physical. It does not authorize a file
name, path, connection factory or configuration key in DB-001B.

## 18. Initial database technology and bounded workload

**Selected technology: SQLite.** PostgreSQL is rejected for the initial
foundation because the repositories contain no driver, service definition,
configuration, tests or operational requirement for it. PostgreSQL remains a
possible future governed target, not an active fallback.

### Bounded initial assumptions

- one local host owns each database;
- exactly one logical HADocs writer service/process opens write transactions;
- multiple threads may request writes only through that serialized owner;
- readers may be concurrent and must keep transactions short;
- independent multi-process writers and remote writers are unsupported;
- scans are periodic, not a continuous high-frequency event stream;
- normalized retained data is bounded to ordinary single-installation Home
  Assistant metadata: design target up to 250,000 current identity-bearing
  objects/relationships and up to 1,000,000 retained normalized observation or
  audit rows before mandatory capacity reassessment;
- at most one scan commit is in progress per installation context;
- long-running read transactions across a scan commit are unsupported;
- WAL may be used, but backups must use a database-consistent mechanism and
  cannot copy only the main file while uncheckpointed WAL state exists.

The numeric limits are explicit architecture bounds for selection and testing,
not claims about observed repository workloads.

### Technology escalation gate

SQLite remains valid while all bounded assumptions hold and lock/busy failures
remain exceptional and recoverable. A governed reassessment is mandatory before
supporting any of:

1. remote or multi-host database access;
2. more than one independent writer process;
3. overlapping scan writers;
4. sustained busy/lock failures after bounded retry;
5. required datasets beyond either stated design bound;
6. operational requirements for server-managed replication/high availability;
7. read workloads that require long transactions concurrent with writes.

Crossing the gate does not automatically select PostgreSQL or permit contract
or schema changes.

## 19. Secret-storage boundary

- Secret ownership belongs exclusively to a protected, installation-local
  secret provider. The operational DB stores a stable opaque handle, secret
  generation/version metadata and non-secret validation state, never secret
  bytes or a reversible representation.
- Prohibited locations include the operational DB, HASK bundle, HUDD, config
  JSON, reports, API/UI payloads, audit text, logs, fixtures, caches and public
  exports.
- The provider must supply confidentiality at rest, integrity, access limited to
  the local HADocs identity service, exact 32-octet retrieval, atomic creation
  and explicit failure. Automatic regeneration is prohibited.
- Windows Credential Manager is verified precedent
  (`security/credential_store.py:79-124`) but does not select the CA-001 provider.
- A concrete protected provider for container/Linux deployments is
  **REQUIRED_BEFORE_IMPLEMENTATION**, because generation, activation, restore
  tests and failure behavior cannot be implemented correctly without it.
- Backup must bind the database, secret generation and protected provenance as
  one labeled recovery set. Restore validates the handle/generation and a
  non-secret cryptographic consistency check before activation.
- Missing, unreadable, malformed, wrong-generation or mismatched secret state
  leaves identity derivation and identity-bearing writes inactive/fail-closed.
  No new secret, scope or public identity may be silently generated.

## 20. Persistence categories

| Category | Authority/mutability | Retention and backup | Scan transaction | Public export / reconstruction / loss |
|---|---|---|---|---|
| A. Protected secret state | Secret provider; mutable only through governed generation/rotation | Retain with logical installation; MUST be consistently backed up with DB/provenance | Referenced/validated before identity writes; not written in scan transaction | Never export; not reconstructable; loss fails closed. |
| B. Mutable current-state projections | HASK operational DB; mutable closed-state projection | Back up with DB; retain current row plus history linkage | Yes, when a complete scan changes state | Sanitized projection may export; rebuild only from complete retained authority; loss fails closed until rebuilt/validated. |
| C. Immutable audit/history | HASK operational DB; append-only after commit | Retain per governed policy, but identity/transition evidence required by architecture cannot be purged | Audit row commits with each governed transition | Sanitized subsets only; authoritative audit not reconstructed from reports; loss fails closed where needed for validation. |
| D. Collision registry/identity history | HASK operational DB; append-only/retained | Indefinite for the logical installation; consistent backup required | Collision check/register is in same identity transaction | Never export raw tuple; cannot reconstruct safely after loss; loss/corruption fails closed. |
| E. Scan/run state | HASK operational DB; running then terminal | Retain enough for lifecycle/audit and idempotency; back up | It is the transaction envelope | Safe summaries may export; running state may recover as interrupted, never as complete. |
| F. Configuration/operator overrides | Existing config/override owners | Back up identity-relevant configuration with recovery set | Read as validated input, not mutated by scan | Export only sanitized; operator-recreatable where identity semantics do not depend on it. |
| G. Derived reports/exports | Output subsystem; replaceable | Optional | No | May export after privacy filtering; may regenerate. Loss does not fail closed. |
| H. Read-only external knowledge | HASK bundle and HUDD | Bundle may be regenerated/reacquired; HUDD may be reacquired with version validation | Read input only | Existing public rules apply; loss deactivates enrichment but does not alter identities. |
| I. Disposable caches | Cache owner; mutable/evictable | No required backup | No authority in transaction | Never identity authority; may reconstruct; loss is safe. |

Current projections (B) and immutable audit/history (C/D) are separate even
when one transaction updates both.

## 21. Invariant allocation

“Defense” is additional enforcement, not a substitute for the primary layer.

| Invariant | Primary layer | Defense | Required failure behavior | Recoverability | Source |
|---|---|---|---|---|---|
| Installation scope uniqueness | DATABASE_CONSTRAINT | TRANSACTION_SERVICE | Reject conflicting context | Recoverable only by explicit conflict resolution; never automatic reassignment | CA-001; Clone Identity |
| One active logical installation context per DB | DATABASE_CONSTRAINT | ARCHITECTURE_ASSERTION | Reject activation | Recoverable by validated operator selection/recovery | Clone Identity |
| Installation-secret reference integrity | SECRET_STORE_BOUNDARY | TRANSACTION_SERVICE | Fail closed | Recoverable only by restoring the matching recovery set | CA-001 Secret Lifecycle |
| Collision registry uniqueness | DATABASE_CONSTRAINT | TRANSACTION_SERVICE | Roll back identity transaction | Input conflict is reviewable; registry corruption requires validated restore | CA-001 Normative Specification |
| Collision history retained after removal | DATABASE_TRIGGER_OR_EQUIVALENT | ARCHITECTURE_ASSERTION | Prohibit delete/purge | Corruption/loss is recoverable only from a validated backup | CA-001; Removal Semantics |
| `source_ref` format | DATABASE_CONSTRAINT | APPLICATION_VALIDATION | Reject malformed write | Recoverable by supplying valid authoritative input | Relationship Correction |
| `source_ref` installation scope | TRANSACTION_SERVICE | DATABASE_CONSTRAINT | Roll back; publish no alias | Recoverable only through a valid same-scope decision, never relabeling | Relationship Correction; CA-001 |
| `source_ref` collision handling | TRANSACTION_SERVICE | DATABASE_CONSTRAINT | Roll back and fail closed | Requires collision investigation or validated recovery; no automatic retry with changed identity | Relationship Correction; CA-001 |
| Entity current-state uniqueness | DATABASE_CONSTRAINT | TRANSACTION_SERVICE | Reject duplicate projection | Recoverable by reconciling against immutable history | Removal Semantics |
| Entity lifecycle transition validity | TRANSACTION_SERVICE | ARCHITECTURE_ASSERTION | Reject transition and retain prior state | Recoverable with new authoritative transition evidence | Removal Semantics |
| HISTORICAL is not a sixth current state | DATABASE_CONSTRAINT | APPLICATION_VALIDATION | Reject invalid state value | Recoverable by writing a valid current state plus separate retention designation | Removal Semantics |
| Relationship tuple uniqueness | DATABASE_CONSTRAINT | TRANSACTION_SERVICE | Treat identical retry idempotently; reject conflict | Identical retry is recoverable; semantic conflict requires authoritative resolution | Relationship Correction |
| Relationship continuity/recreation | TRANSACTION_SERVICE | ARCHITECTURE_ASSERTION | Reject ambiguous recreation | Recoverable only with authoritative continuity/discontinuity evidence | Relationship Correction; Removal Semantics |
| Prevent cross-installation aliasing | TRANSACTION_SERVICE | DATABASE_CONSTRAINT | Fail closed; publish no reference | Not automatically recoverable; requires valid classification/recovery | CA-001; Clone Identity |
| Scan completeness before absence transitions | TRANSACTION_SERVICE | DATABASE_CONSTRAINT | Reject absence-derived transition without complete terminal run | Recoverable by a later successful complete scan | Removal Semantics |
| Failed/partial scan cannot infer removal | ARCHITECTURE_ASSERTION | TRANSACTION_SERVICE | Persist run failure only and preserve current state | Recoverable by a later complete scan; no correction needed to preserved state | Removal Semantics |
| Clone classification precedence | TRANSACTION_SERVICE | APPLICATION_VALIDATION | Return UNKNOWN and fail closed on ambiguity | Recoverable only with higher-authority evidence or explicit recovery | Clone Identity |
| Clone activation outcome | TRANSACTION_SERVICE | ARCHITECTURE_ASSERTION | Do not activate non-authorized/unknown context | Recoverable only after a valid classification outcome | Clone Identity |
| Compatibility fail-closed outcomes | APPLICATION_VALIDATION | TRANSACTION_SERVICE | Record outcome and prohibit incompatible capability | Recoverable after compatible versions/evidence are provided | Version Compatibility |
| Schema-version compatibility | MIGRATION_VALIDATION | DATABASE_CONSTRAINT | Refuse write/startup for unsupported version | Recoverable through governed migration or compatible implementation/restore | DB001-D-008; Version Compatibility |
| Audit evidence immutability | DATABASE_TRIGGER_OR_EQUIVALENT | ARCHITECTURE_ASSERTION | Reject update/delete | Corruption/loss is recoverable only from validated immutable backup | AI-002 specifications |
| Secret non-disclosure | SECRET_STORE_BOUNDARY | APPLICATION_VALIDATION | Reject operation and emit only safe error code | Exposure is not reversed by retry; requires security response and governed rotation/recovery | CA-001 |

Count: **22 invariant allocations**. Structural rules are not delegated solely
to application code. “Trigger or equivalent” permits append-only database
permissions/structures to be chosen during schema design without prescribing
executable SQL here.

## 22. Conceptual transaction model

| Transaction | Atomic inputs and writes | Never on failure | Idempotency / fail-closed / audit |
|---|---|---|---|
| Installation activation | Valid DB/schema, installation context, secret handle/generation validation, provenance, compatibility and activation audit | No active-context switch or public identity emission | Key: activation request + context/generation; any mismatch fails closed; audit required. |
| Successful complete scan | Terminal complete run, normalized observations, current projections, lifecycle transitions, relationship changes and audit | No partial projection/history commit | Key: scan/snapshot ID; one commit; complete authority required for absence transitions. |
| Partial/failed scan | Run terminal status, safe error/capability evidence and audit only | No bulk NOT_OBSERVED, REMOVED, IDENTITY_INVALID, relationship deletion or current-state replacement due to absence | Key: scan ID; retry may complete a new attempt; preserve prior projections. |
| Entity lifecycle transition | Prior current row, authoritative event/complete-scan evidence, new current state and immutable transition audit | No state change without matching audit | Key: entity reference + evidence/run + target state; invalid/ambiguous transition rejects. |
| Relationship replacement/recreation | Prior tuple/history, authoritative new tuple, reference validation, current projection and audit | No deletion without retained history; no ambiguous reference reuse | Key: relationship identity + evidence/run; continuity rules fail closed. |
| Collision check/registration | Validated secret context, canonical private tuple, candidate reference, uniqueness check, registry entry and identity publication state | Never publish/store current identity without registry commit | Key: format/kind/scope/canonical tuple; collision or registry failure rolls back; audit safe metadata only. |
| Clone classification/activation | Declaration, protected provenance, supporting evidence, precedence result, context continuity/discontinuity and audit | No secret/scope rotation or activation on UNKNOWN without authorized recovery | Key: classification request/evidence set; secret access occurs before DB commit and is never copied into it. |
| Compatibility decision | Version dimensions, negotiated classification, capability state and audit | No incompatible capability activation | Key: context + version tuple; unknown/incompatible follows defined fail-closed result. |
| Migration | Consistent backup marker, current version, ordered step, transformed state, target version and migration audit | No target version marker before all validation passes | Key: from/to version; exclusive writer; interruption rolls back or remains explicitly incomplete and blocks startup. |

SQLite transactions cannot atomically commit an external secret-provider write.
Secret creation/rotation therefore uses a recoverable coordination protocol:
prepare and validate protected secret state, commit DB metadata/provenance, then
activate only after post-commit consistency validation. Any intermediate state
remains inactive and recoverable; it never silently generates identities.

## 23. Initial concurrency model

- One configured local SQLite file represents one HASK operational store.
- Exactly one logical writer service/process owns write transaction sequencing.
- Multiple application threads may submit commands, but cannot independently
  open competing write units outside that owner.
- Concurrent short-lived readers are supported against committed snapshots.
- Write transactions and reads spanning writer commits must be short; long-lived
  read snapshots are unsupported initially.
- Busy/locked handling uses bounded retry with jitter/backoff at the future
  transaction boundary. Exhaustion fails the operation without partial state;
  it never downgrades an invariant. Exact counts/timing are implementation
  configuration and require tests.
- Independent multi-process writers, network filesystems, remote database
  access, overlapping scan commits and direct ad-hoc writers are prohibited.
- WAL is an operational option consistent with existing HADocs practice, not a
  license to copy a live main file without its transactional state.

## 24. Backup and restore consistency

| Component | Classification | Restore rule |
|---|---|---|
| HASK operational DB | MUST_BE_CONSISTENTLY_BACKED_UP | Restore only with matching secret/provenance set; run integrity/schema/identity checks before activation. |
| Installation-local secret | MUST_BE_CONSISTENTLY_BACKED_UP and MUST_NOT_BE_BUNDLED in public/general exports | Restore through protected provider; never place bytes in DB/report archive. |
| Protected provenance | MUST_BE_CONSISTENTLY_BACKED_UP | Validate integrity and lineage with DB context. |
| Identity-relevant operator configuration | MUST_BE_CONSISTENTLY_BACKED_UP | Validate declared context/secret handle; unrelated preferences may be restored separately. |
| Generated reports/exports | OPTIONAL / MAY_BE_REGENERATED | Never used to reconstruct authority. |
| HUDD database | MAY_BE_REACQUIRED | Validate HUDD version/checksum; not part of identity recovery. |
| HASK bundle | MAY_BE_REGENERATED or MAY_BE_REACQUIRED | Revalidate via PI1 trust boundary; bundle version does not replace DB recovery data. |
| Disposable caches | OPTIONAL | Discard and rebuild. |

Restore validation requires: SQLite integrity, supported schema version, one
active context invariant, collision-registry availability, secret
handle/generation match, protected-provenance integrity, compatibility decision
and absence of incomplete migration. Any missing, unrelated or mismatched
identity component leaves the capability inactive/fail-closed. Automatic secret
regeneration, scope reassignment or public-reference replacement is prohibited.

## 25. Migration foundation

- Initial schema version convention: positive monotonically increasing integer,
  starting at **1** when an executable schema is later authorized.
- The operational DB stores exactly one current schema-version record plus an
  immutable ordered migration audit. This does not define table names.
- Migration identifiers are zero-padded ordered integers conceptually
  (`0001`, `0002`, ...); gaps, duplicates and reordering are invalid.
- Each migration is exclusive-writer, transactional and validates source and
  target invariants. A consistent recovery set is required before destructive
  or identity-affecting transformation.
- Startup accepts only a schema version explicitly supported by that
  implementation. A newer/unknown forward version is read/write rejected and
  fails closed; it is never downgraded automatically.
- Interrupted migration rolls back where the engine permits. Otherwise an
  explicit incomplete marker blocks normal activation until governed recovery.
- Automatic down-migration is prohibited. Rollback posture is restore of the
  pre-migration consistent recovery set plus the prior compatible implementation.
- Migration audit records from-version, to-version, migration identity,
  implementation version, timestamps/status and safe validation result—never
  secret or raw public-identity inputs.

Independent version dimensions:

| Dimension | Owner / effect |
|---|---|
| Database schema version | HASK operational DB migration compatibility only. |
| Public contract version | Metadata producer/consumer contract; remains `1.0.0`. |
| Architecture version | Accepted architectural semantics, including CA-001/AI-002. |
| Implementation version | HADocs release/build implementing a supported schema. |
| HASK knowledge schema version | HASK authoritative record/bundle build domain. |
| HUDD schema version | Separate HUDD read-only knowledge database lifecycle. |

No version implies compatibility in another dimension.

## 26. DB-001A gap disposition

| Gap | DB-001B disposition | Result |
|---|---|---|
| DB001-G-001 | RESOLVES | Separate logical installation operational context from scan aggregate. |
| DB001-G-002 | RESOLVES | Installation-wide retained collision-registry category and atomic registration are mandatory. |
| DB001-G-003 | RESOLVES | Separate mutable current projections from immutable lifecycle/history. |
| DB001-G-004 | RESOLVES | Complete-run authority gates absence transitions; failed/partial runs preserve state. |
| DB001-G-005 | BOUNDS | Single local writer and explicit workload/escalation limits permit initial SQLite selection. |
| DB001-G-006 | RESOLVES | Defines DB + matching secret + provenance + identity configuration recovery unit. |
| DB001-G-007 | DEFERS_TO_SCHEMA_DESIGN | Ordered independent schema migration architecture is fixed; executable form awaits authority. |
| DB001-G-008 | DEFERS_TO_IMPLEMENTATION | Abstract boundary fixed; concrete non-Windows provider is REQUIRED_BEFORE_IMPLEMENTATION. |
| DB001-G-009 | DEFERS_TO_IMPLEMENTATION | Separate repository boundary will be planned; no repository code authorized. |
| DB001-G-010 | RESOLVES | Nine conceptual atomic transaction boundaries and failure rules defined. |
| DB001-G-011 | RESOLVES | HUDD explicitly remains separate/read-only. |
| DB001-G-012 | RESOLVES | History JSON remains a derived projection; no import or authority role. |
| DB001-G-013 | DEFERS_TO_SCHEMA_DESIGN | Indexes/retention/checkpoint details follow canonical keys and bounded workload. |
| DB001-G-014 | DEFERS_TO_IMPLEMENTATION | Raw cache remains disposable/non-authoritative; cleanup is implementation policy. |

All fourteen gaps remain visible. None requires external policy before the next
schema-design batch, though product decisions can later revise bounded workload
assumptions through governance.

## 27. Resolution of DB-001A factual questions

| Question | Classification | DB-001B treatment |
|---|---|---|
| Deployment modes | RESOLVED_BY_BOUNDED_ASSUMPTION | Windows desktop and local Docker/container are initial targets; HA add-on-specific support is not claimed and MAY_BE_DEFERRED. |
| Concurrent writers | RESOLVED_BY_BOUNDED_ASSUMPTION | One logical local writer; independent multiprocess writers unsupported. |
| Size/frequency/retention | RESOLVED_BY_BOUNDED_ASSUMPTION | Periodic scans and stated row bounds select technology; exact retention is REQUIRED_BEFORE_IMPLEMENTATION, not schema identity. |
| Non-Windows secret provider | REQUIRED_BEFORE_IMPLEMENTATION | Provider must be selected and verified before secret-dependent code/tests. |
| Backup/restore unit | RESOLVED_BY_BOUNDED_ASSUMPTION | DB + matching secret + protected provenance + identity-relevant configuration. |
| Observation retention breadth | REQUIRED_BEFORE_SCHEMA | Schema design must identify minimum transition/audit fields and an explicit optional retention policy; blanket raw retention is prohibited. |
| Existing history JSON import | MAY_BE_DEFERRED | Remains derived; no import in initial foundation. |
| General vs separate DB | RESOLVED_BY_BOUNDED_ASSUMPTION | Separate writable HASK operational SQLite file selected. |

The sole unresolved item required before table-level schema completion is the
normalized-observation retention boundary: the schema must distinguish required
transition/audit evidence from optional diagnostic history without persisting
raw sensitive payloads.

## 28. DB-001B next-batch input record

At DB-001B closure, the next work was expected to resolve retention and then
prepare relational design. DB-001C sections 30–38 now resolve item 1 below and
supersede the batch label; the remaining items move to the DB-001D recommendation
in section 38.

1. resolve the normalized-observation retention boundary;
2. propose conceptual tables, keys, relationships and current/history split;
3. map all 22 invariants to concrete declarative constraints or service checks;
4. specify repository interfaces and transaction orchestration without code;
5. specify indexes and retention classes against the bounded workload;
6. trace migrations from conceptual schema version 1 without creating SQL.

## 29. Updated traceability and validation

| DB-001B requirement | Decision/source |
|---|---|
| Exactly one operational boundary | DB001-D-001 and DB001-D-002 |
| Exactly one initial technology | DB001-D-003 and section 18 |
| Bounded writer topology | DB001-D-004 and section 23 |
| Secret outside ordinary DB/output | DB001-D-005 and section 19 |
| Current/history separation | Sections 20-22; AI-002 Removal Semantics |
| Failed/partial scan safety | Sections 21-22; AI-002 Removal Semantics |
| Backup consistency | DB001-D-006 and section 24; CA-001 recovery |
| Invariant layers | DB001-D-007 and section 21 |
| Independent migration/version model | DB001-D-008 and section 25; AI-002 Version Compatibility |
| All DB-001A gaps retained | Section 26 |

Validation result:

| Check | Result |
|---|---|
| Initial technology selected exactly once | PASS — SQLite |
| Operational boundary selected exactly once | PASS — separate HADocs-owned HASK operational SQLite file |
| HASK, HUDD and operational state separated | PASS |
| All 14 gaps dispositioned | PASS |
| Accepted invariants allocated | PASS — 22 |
| Failed/partial scans cannot cause absence-derived removal/invalidation | PASS |
| Current projection and immutable history separated | PASS |
| Secret excluded from ordinary DB/public output | PASS |
| Schema and contract versions separated | PASS |
| Contract `1.0.0` remains active; `2.0.0` inactive | PASS |
| Executable schema/migration created | NO |
| Code/runtime/tests/fixtures/dependencies/config changed | 0 |
| CA-001/AI-002/DF-002 changed | 0 |
| Implementation authorized or started | NO |

The DB-001B validation above remains preserved. DB-001C below builds on it
without reopening any DB-001B decision.

## 30. DB-001C observation-retention decisions

| ID | Decision | Reason | Consequence | Revisit trigger |
|---|---|---|---|---|
| DB001-D-009 | Every normalized persisted observation record has exactly one primary taxonomy class A–L, assigned by its stored role using the precedence in section 31. | Prevents one record from receiving conflicting authority, privacy or retention semantics. | A source fact may produce separate records with separate roles, but one stored record cannot cross classes. | A future governed observation role cannot be classified without overlap. |
| DB001-D-010 | The class-to-policy mapping in section 32 is closed and normative for the initial foundation. | Retention must follow architectural necessity rather than incidental collector behavior. | Required identity/audit state is retained; diagnostics and derived data cannot silently become authority. | Proven legal/product retention obligations or capacity evidence require governed change. |
| DB001-D-011 | Only validated, privacy-minimized, typed normalized facts may enter operational persistence; raw collector payloads are discarded after normalization. | Raw payloads are broad, sensitive and unsuitable as deterministic identity evidence. | Debugging cannot depend on a retained raw payload; collectors must emit safe normalized results/errors. | A separately governed, privacy-reviewed forensic facility outside identity authority. |
| DB001-D-012 | Reproducible decisions retain immutable source references, normalized decision inputs, authority/provenance, prior and resulting state, decision/rule/version context and outcome. | A current projection alone cannot explain or replay an identity-bearing transition. | Clone, identity, relationship, removal, compatibility and activation decisions remain auditable. | Independent review proves a listed field unnecessary without reducing reproducibility. |
| DB001-D-013 | Secrets and raw identifiers never enter operational observations; public export is allowlist-based, and internal installation identifiers/provenance remain non-public. | Preserves CA-001 secrecy, unlinkability and AI-002 privacy constraints. | Internal retention does not imply export permission. | A governed privacy architecture amendment. |
| DB001-D-014 | Retention lifecycle is class-specific: supersession never erases required audit/collision history, and deletion requires an allowed class outcome plus referential/audit validation. | Current state, history, audit, diagnostics and temporary data have different authority. | Purge cannot silently change identity or make transitions irreproducible. | A governed retention policy with equivalent invariant preservation. |

These decisions define what is retained. They do not define tables, columns,
SQL, repository interfaces, executable migrations or implementation behavior.

## 31. Closed observation taxonomy

An “observation record” here means a normalized persistence candidate, not an
unfiltered API response. Classification occurs after validation and before any
durable write. The first matching role in the precedence column is the sole
primary class. If one collected fact serves several roles, the transaction may
materialize distinct linked records; it may not give one record multiple
primary classes.

| Class | Primary role and exclusive boundary | Classification precedence |
|---|---|---|
| A. Identity-bearing observations | Validated canonical identity input metadata, opaque reference result metadata, reference kind and installation-scope association necessary to preserve identity/collision behavior. Excludes secret bytes and raw identifiers from public/ordinary observation storage. | 1 |
| D. Transition evidence | A normalized authoritative fact selected as an input to a specific clone, identity, relationship, removal or activation transition. It is the evidence copy/reference for that decision, not the mutable current projection. | 2 |
| E. Compatibility observations | Version-dimension facts and normalized capability evidence used to decide compatible, conditionally compatible, incompatible or unknown. | 3 |
| C. Relationship observations | Current normalized relationship tuple and resolution fact not already materialized as transition evidence. | 4 |
| B. Lifecycle observations | Current normalized entity/identity availability or lifecycle fact not already selected as transition evidence. | 5 |
| F. Audit evidence | Decision envelope: authority, provenance, rule/architecture/schema/contract context, idempotency identity, prior/result references and outcome. It does not duplicate the source fact classified as D/E. | 6 |
| G. Operational diagnostics | Privacy-minimized counters/status needed to operate the persistence capability but not to decide identity or lifecycle. | 7 |
| H. Debug-only diagnostics | Verbose troubleshooting material with no operational or architectural authority. | 8 |
| I. Raw collector payloads | Unnormalized REST/WebSocket/collector responses or arbitrary source payloads. | 9 |
| J. Derived values | Values calculable from authoritative retained state, such as counts or presentation summaries. | 10 |
| K. Temporary runtime values | In-flight buffers, locks, retry state and intermediate calculations meaningful only during one process/transaction. | 11 |
| L. Reconstructable values | Validated non-authoritative projections that can be reacquired or deterministically rebuilt from retained authority/external read-only sources and are not J/K. | 12 |

The order is role precedence, not importance. Audit envelopes (F) remain their
own records; source facts referenced by them retain their earlier class. No
record may be persisted as “unclassified.” An unknown role is rejected from
durable persistence until classified through governance.

## 32. Retention-class mapping

Exactly one policy applies to every taxonomy class.

| Observation class | Sole retention policy | Why / authority | Replay and audit | Privacy and storage | Reconstruction |
|---|---|---|---|---|---|
| A. Identity-bearing | MUST_RETAIN | CA-001 collision/identity continuity requires installation-lifetime identity history. | Required for collision verification and stable identity replay. | Internal; opaque output metadata may be allowlisted, canonical private inputs never exported; compact but non-purgeable. | Cannot be safely reconstructed after authoritative loss. |
| B. Lifecycle | RETAIN_UNTIL_SUPERSEDED | AI-002 requires one deterministic current state. | Current projection supports the next transition; transition evidence/history is D/F. | Internal by default; sanitized current state may export; one current projection per identity. | May be rebuilt only from retained D/F evidence or a new complete authoritative scan. |
| C. Relationship | RETAIN_UNTIL_SUPERSEDED | AI-002 requires one deterministic current relationship projection and stable `source_ref`. | Current tuple supports continuity; replaced/deleted state is preserved through D/F and identity history. | Opaque refs may be allowlisted; no raw identifiers; bounded current projection. | May be rebuilt only from retained evidence or a complete authoritative collection. |
| D. Transition evidence | RETAIN_FOR_AUDIT | AI-002 deterministic transition and DB001-D-012. | Append-only evidence is required; current projection alone is insufficient. | Internal, privacy-minimized, potentially installation-identifying; storage grows with governed transitions. | Not replaced by later observation; loss requires validated restore where decision replay is required. |
| E. Compatibility | RETAIN_FOR_AUDIT | AI-002 Version Compatibility requires reproducible fail-closed outcomes. | Retain each decision input with its run/activation audit. | Internal version/capability metadata; sanitized compatibility result may export. | A future check does not reproduce the historical decision environment. |
| F. Audit | MUST_RETAIN | DB-001B audit immutability and all accepted AI-002 decision chains. | Append-only minimum audit is mandatory for deterministic explanation. | Internal; only safe allowlisted summaries export; compact mandatory metadata. | Cannot be regenerated from reports/current projection. |
| G. Operational diagnostics | CONFIGURABLE_HISTORY | Useful for operations but not architecture authority. | Not required for identity replay; retention window may be configured. | Must be privacy-minimized/redacted; bounded by configured expiry. | May be observed again; historical loss is acceptable. |
| H. Debug-only diagnostics | DO_NOT_RETAIN | No operational authority and elevated leakage risk. | No replay/audit requirement. | Must not enter DB, reports or durable logs through this boundary. | Reproduce only by an explicitly authorized future debug session. |
| I. Raw collector payloads | DO_NOT_RETAIN | DB001-D-011; raw values are excessive and may include secrets/PII. | Never evidence merely because captured; normalized D/E facts carry required evidence. | Discard after normalization; never export or persist. | Reacquire from source if authorized; absence is not an identity failure. |
| J. Derived values | REGENERATE_WHEN_REQUIRED | They are functions of retained authoritative state. | Not required for replay; derivation version belongs in output/audit when material. | Public export only under projection policy; no canonical storage cost. | Deterministically regenerate. |
| K. Temporary runtime values | MEMORY_ONLY | Meaning is transaction/process-local. | No historical value. | Never export; released at transaction/process end. | Recreated by executing the operation again. |
| L. Reconstructable values | REGENERATE_WHEN_REQUIRED | Authoritative source or retained inputs remain available. | Not required for transition replay. | Apply source privacy policy on reconstruction/export; no mandatory storage. | Reacquire or rebuild after loss. |

Seven of the eight allowed retention policies are used. `OPTIONAL_HISTORY` is
intentionally unused: optional durable history without an explicit configured
window would create ambiguous retention. A future use requires governance.

## 33. Current state, history and authority separation

| Architectural category | Taxonomy owner | Meaning | Mutability |
|---|---|---|---|
| Current projection | B and C | Exactly one latest lifecycle/relationship projection used for current decisions. | Replaced atomically by valid transitions. |
| Historical record | D plus retained A identity history | Time-ordered normalized facts necessary to preserve/reproduce identity-bearing transitions. | Append-only after commit. |
| Audit evidence | F, with E for compatibility input | Decision envelope and versioned authority/provenance explaining why a transition/outcome occurred. | Append-only/immutable. |
| Diagnostic history | G | Optional configured operational trend; never transition authority. | Append and expire under configured policy. |
| Temporary runtime state | K (and non-retained H/I before discard) | In-flight data with no durable authority. | Memory-only and disposable. |
| Reconstructable state | J and L | Projection/output that can be rebuilt or reacquired. | Not canonical; regenerate rather than retain. |

Each class has one primary category. A current B/C row may reference immutable
D/F records, but it does not become history or audit itself. Superseding a
projection never deletes its supporting history.

## 34. Minimum transition evidence

“Minimum fields” are conceptual information requirements, not schema columns.
Every decision also retains a safe audit identity and its architecture,
contract, implementation and schema-version context where applicable.

| Transition | Minimum retained information | Minimum duration | Append-only? | Is current projection sufficient? |
|---|---|---|---|---|
| Clone decision | Logical-installation reference; classification request ID/time; authoritative declaration reference; protected-provenance reference/integrity status; supporting platform/concurrency evidence references; precedence result; ambiguity state; classification and activation outcome; prior/new scope and secret-generation references without secret bytes. | Logical-installation lifetime and through any retained descendant identity history. | Yes, D/F. | No. |
| Identity transition | Identity/reference kind; installation scope; CA-001 format/generation metadata; prior/result opaque reference metadata; collision-registry decision; authoritative trigger; prior/result lifecycle state; run/time and outcome. | For as long as the collision registry or any related identity/history exists; effectively installation lifetime. | Yes, A/D/F and collision history. | No. |
| Relationship transition | Relationship identity/predicate; source/target opaque refs; prior/result tuple; continuity/recreation classification; authoritative source capability/evidence; run/time; deletion/replacement outcome. | For as long as either identity, relationship history or audit dependency is retained. | Yes, D/F; current C is replaceable. | No. |
| Removal transition | Identity ref; prior current state; normalized complete-scan or positive-removal evidence; scan completeness/status; absence category; resulting ACTIVE/NOT_OBSERVED/UNAVAILABLE/REMOVED/IDENTITY_INVALID state; HISTORICAL designation; time/outcome. | At least while identity/collision/history is retained; removal evidence cannot expire while it explains current/history state. | Yes, D/F. | No. |
| Compatibility decision | All compared version dimensions; supported ranges/capability evidence; compatible/conditional/incompatible/unknown result; fail-closed capability outcome; run/activation reference and time. | Through the associated activation/run retention and any audit referencing the decision. | Yes, E/F. | No. |
| Activation outcome | Logical-installation/context reference; clone and compatibility decision refs; secret-handle/generation validation status; provenance integrity status; requested/result state; safe failure code; time/idempotency identity. | Logical-installation lifetime for identity activation; failed attempts per mandatory audit policy. | Yes, F with referenced D/E. | No. |

Raw source payloads, credentials, secret material and raw identifiers are never
part of minimum evidence. Evidence references must resolve to retained,
privacy-minimized normalized records or protected provenance.

## 35. Normalization boundary

Before persistence, a collector result SHALL pass all of these gates:

1. capability/source and collection-run identity validation;
2. explicit completeness/partial/failure classification;
3. allowlist extraction of fields required by the assigned A–G role;
4. type, enum, version, timestamp and reference validation;
5. secret, credential, raw-identifier and unnecessary PII exclusion;
6. canonical encoding/reference derivation through accepted CA-001 boundaries;
7. provenance/authority and privacy classification;
8. deterministic taxonomy classification and sole retention-policy assignment;
9. transaction eligibility and invariant validation.

Raw payloads are transient input only. They are **always discarded after the
normalization attempt** in this operational foundation, whether normalization
succeeds or fails. A failure persists only an allowlisted safe error/capability
record where required. Existing optional raw-cache behavior remains outside the
operational identity store, is non-authoritative, and is not expanded or
endorsed by DB-001C.

## 36. Privacy and export boundary

| Class | Secret allowed? | PII / installation identifiers | Opaque references | Export rule |
|---|---|---|---|---|
| A | Never | Internal installation scope/reference metadata only; raw ID excluded from ordinary observation/export | Expected | Allowlist opaque public identity metadata only; canonical private tuple/internal scope not exported. |
| B | Never | Minimize; names/user metadata excluded unless separately authorized | Allowed | Sanitized current lifecycle state may export. |
| C | Never | Raw endpoints/IDs excluded | Required for source/target | Allowlist predicate and opaque refs only. |
| D | Never | May contain privacy-minimized internal installation evidence refs | Allowed internally | Internal; export only a safe summarized evidence status, never private evidence inputs. |
| E | Never | Normally version/capability metadata; installation/run refs internal | Optional internal refs | Sanitized version/result may export. |
| F | Never | Internal provenance, run and decision references | Allowed internally | Safe audit summary only; protected provenance remains internal. |
| G | Never | Must be minimized/redacted | Only when necessary for safe correlation | Internal by default; aggregated safe diagnostics may export. |
| H | Never | May be sensitive; therefore not durable | Not durably retained | Never export through this foundation. |
| I | May arrive containing secrets/PII, which is why it is rejected from persistence | Unbounded/untrusted | Untrusted | Never persist or export. |
| J | Never as an input | Inherits strictest source classification | May contain allowlisted refs | Export only through the projection's allowlist/redaction policy. |
| K | Must not retain secrets beyond the minimum protected operation boundary | Process-local only | Possible transiently | Never export. |
| L | Never in retained form | Inherits source policy | As required by regenerated projection | Reapply current privacy policy on each reconstruction/export. |

No taxonomy class authorizes secret persistence in SQLite. Class I describes
what may be present at an untrusted input boundary, not permission to retain it.

## 37. Retention lifecycle

| Class | Creation | Replacement/supersession | Expiration/deletion | Historical preservation / reconstruction |
|---|---|---|---|---|
| A | On validated identity registration/collision transaction | Never overwrite identity history; new generation/format is a new retained context | Deletion prohibited while logical installation or any dependent history exists | Preserve installation lifetime; no reconstruction after loss. |
| B | On first authoritative current lifecycle fact | Atomically replace only through valid transition | Prior projection may cease being current after D/F commit; current row cannot expire by time alone | Rebuild only from retained evidence or new complete scan. |
| C | On authoritative relationship creation | Atomically replace/delete current tuple under relationship rules | Superseded current projection may be removed only after D/F history commits | Rebuild only from retained evidence or complete collection. |
| D | With the governed transition it supports | Never replace; correction is a new linked evidence record | Deletion prohibited while referenced or architecture-required | Append-only history. |
| E | With each compatibility decision | Never rewrite historical input/result | May delete only when no activation/run/audit depends on it and governed audit minimum permits | Historical decision is not reconstructed from current versions. |
| F | With every governed decision/transition | Never replace; append corrective audit | Deletion prohibited for mandatory identity/transition audit | Restore only from validated backup. |
| G | On privacy-minimized operational event | Append; aggregation may supersede detail only under configured policy | Expire/delete at configured boundary if unreferenced by D/F | Loss acceptable; observe again. |
| H | May exist during explicit runtime debugging | No durable replacement | Destroy at session/operation end; durable creation prohibited | Not reconstructed as history. |
| I | Exists only before/while normalization | Never supersedes authority | Discard immediately after normalization attempt | Reacquire only from source under a future authorized collection. |
| J | Generate for request/report | Replace freely with same-input/version deterministic result | Delete freely | Regenerate from retained authority. |
| K | Create inside operation/transaction | Replace freely in memory | Destroy on commit, rollback, cancellation or process exit | Recreate by retry. |
| L | Generate/acquire when needed | Replace when source/version changes | Delete freely if not referenced as authority (which is prohibited) | Reacquire/rebuild and revalidate. |

Deletion is never allowed merely because elapsed time passed when a record is
needed by collision history, protected lineage, a current projection or an
immutable decision chain. A purge operation must prove no prohibited reference
or invariant loss; otherwise it fails closed.

## 38. DB-001C closure and next-batch gate

DB-001C resolves the DB-001B `REQUIRED_BEFORE_SCHEMA` question: persist the
minimum normalized A–F facts required for current state, identity/collision
continuity and reproducible decisions; retain G only under explicit configured
history; do not persist H/I/K; regenerate J/L.

Validation:

| Check | Result |
|---|---|
| Observation taxonomy is closed and exclusive | PASS — 12 classes |
| Every class has exactly one retention policy | PASS |
| Distinct retention policies used | 7 of 8 allowed; `OPTIONAL_HISTORY` intentionally unused |
| New stable decisions | PASS — DB001-D-009 through DB001-D-014 (6) |
| Every AI-002 persistence concept retains a location | PASS — DB-001B section 9 plus A–F mapping |
| Current state/history/audit remain separate | PASS |
| Minimum transition evidence is reproducible | PASS |
| Raw payload becomes authority or durable state | NO |
| Secret enters operational DB/public output | NO |
| Schema/table/SQL design introduced | NO |
| Repository interface introduced | NO |
| Technology/boundary/writer/secret/transaction/invariant decisions reopened | NO |
| Contract `1.0.0` active; proposed `2.0.0` inactive | PASS |
| Implementation authorized or started | NO |

Remaining blockers before conceptual relational schema design: **none**.
Concrete non-Windows secret-provider selection remains required before
implementation, not before schema design.

Recommended next batch: **DB-001D — Canonical conceptual relational model,
keys and repository boundaries**. It may define non-executable entities,
relationships, keys, constraint mapping and repository responsibilities, but
must not create SQL, migrations, code, dependencies, tests or configuration.

The DB-001C validation above remains preserved. DB-001D below consumes it
without reopening any DB-001A–C decision.

## 39. DB-001D canonical-model decisions

| ID | Decision | Reason | Consequences | Future revisit trigger |
|---|---|---|---|---|
| DB001-D-015 | The operational model has ten aggregate roots: LogicalInstallation, CollisionRegistry, Entity, Relationship, ScanRun, Observation, CompatibilityDecision, AuditRecord, VersionState and MigrationState. | These are the independently identified consistency/lifecycle boundaries required by CA-001, AI-002 and DB-001A–C. | All other operational concepts are owned entities, value objects, reference objects or derived views with one owner. | A governed architecture proves a required atomic consistency boundary cannot be represented by these roots. |
| DB001-D-016 | Canonical installation identity belongs only to LogicalInstallation; public identity belongs to accepted opaque identity registrations; source_ref is a value of an Entity/Relationship endpoint identity and never a raw external ID. | Prevents scan aggregates, clone evidence, external IDs and relationship rows from competing as identity authorities. | Clone continuity changes context/activation state, not ownership of canonical installation identity. | A future accepted identity architecture replaces CA-001/AI-002. |
| DB001-D-017 | Relationships link roots by stable conceptual references and multiplicities; ownership is never inferred from a graph edge. | Separates referential association from aggregate ownership and avoids duplicate persistence. | Cross-root changes use DB-001B transaction boundaries; no foreign-key design is implied. | Physical design demonstrates an unresolvable consistency conflict. |
| DB001-D-018 | One conceptual repository owner exists per aggregate root; repositories own roots and their owned members, not cross-context external data. | Gives one write authority per aggregate without defining interfaces. | Transaction orchestration may coordinate owners but cannot bypass aggregate rules. | A later governed unit-of-work design combines ownership without weakening boundaries. |
| DB001-D-019 | Current projections are owned mutable entities; history is immutable owned events/observations; audit is a separate immutable aggregate; read models may join them but do not duplicate authority. | Preserves DB-001B/C current/history/audit separation. | Supersession changes current projection and appends history/audit atomically. | A governed retention amendment with equivalent replay guarantees. |
| DB001-D-020 | Operational entities live only in the separate HADocs-owned HASK operational context; HUDD, HASK bundle, secret storage, configuration and generated output remain distinct bounded contexts connected only by explicit external references/projections. | Maintains failure, migration, privacy and authority isolation. | External knowledge/secret/config data is never silently copied into operational authority. | A future governance transition explicitly changes a bounded-context contract. |

## 40. Aggregate and concept classification

### 40.1 Aggregate roots

| Aggregate root | Purpose and authority | Identity and lifecycle | Mutability / retention / recovery |
|---|---|---|---|
| LogicalInstallation | Canonical authority for one logical installation, its context lineage, clone decisions and activation outcomes. | Stable internal synthetic identity; no natural hardware identity and no public raw identity. Created by authoritative initialization; remains through migration/restore; discontinuity creates a distinct root. | Root metadata/current context is mutable only through governed decisions; lineage/decisions are retained audit history. Recovery requires matching DB, secret generation and protected provenance. |
| CollisionRegistry | Installation-scoped authority for accepted opaque identity registrations and collision history. | Stable internal registry identity associated with exactly one LogicalInstallation and context scope. Exists for the logical-installation lifetime. | Append-only identity history; current registration status may evolve without deleting history. Loss/corruption fails closed and requires validated restore. |
| Entity | Authority for one installation-scoped runtime entity identity and its current lifecycle projection. | Internal synthetic identity; public identity is the accepted opaque registration reference; private natural identity is represented only through the collision/identity boundary. | Current state is mutable by valid transition; lifecycle events are immutable; retained while identity/collision/history remains. |
| Relationship | Authority for one logical relationship identity, current tuple and continuity/recreation history. | Internal synthetic identity; public identity follows accepted relationship-ID semantics. Its source endpoint is the accepted opaque entity reference and its target follows frozen target-reference semantics. Natural uniqueness is the accepted `(predicate, source_ref, target_ref)` tuple, not raw IDs. | Current tuple/status changes only through relationship transition; events are immutable. Recovery uses source identity validation plus relationship history. |
| ScanRun | Authority for one collection attempt, completeness and terminal outcome. | Transient-at-creation synthetic run identity that becomes stable audit reference. Lifecycle is running to exactly one terminal complete/partial/failed outcome. | Mutable only until terminal; terminal state retained per audit dependency. Interrupted state recovers as non-complete, never silently complete. |
| Observation | Authority for one normalized classified observation persistence record. | Stable internal synthetic observation identity linked to one ScanRun; no public identity unless an allowlisted projection exists. | Immutable after commit; retention follows its sole DB-001C A–L policy. Invalid/raw candidates never become roots. |
| CompatibilityDecision | Authority for one evaluated compatibility result and capability boundary. | Stable internal synthetic decision identity scoped to version inputs, context and request/run. | Immutable after commit; later evaluations create new roots. Recovery uses retained decision inputs and audit. |
| AuditRecord | Authority for one immutable decision/transition audit envelope. | Stable synthetic audit identity and idempotency correlation; never a public domain identity. | Append-only and non-deletable while architecture-required. Restore from validated immutable backup only. |
| VersionState | Authority for the operational store's currently recognized independent version dimensions. | Singleton conceptual root per operational DB, with stable internal identity; versions remain distinct. | Changes only through compatibility/migration governance; retained changes are audited. Unsupported state fails closed. |
| MigrationState | Authority for migration eligibility, in-progress/terminal status and ordered migration history. | Singleton current migration coordinator plus immutable attempt identity/history per operational DB. | Current coordination state is mutable only during exclusive migration; attempt history is immutable. Interrupted/unknown state blocks normal activation. |

### 40.2 Owned entities

| Owned entity | Sole owner | Purpose / lifecycle / retention |
|---|---|---|
| InstallationContext | LogicalInstallation | Holds one scoped operational identity context and secret-generation reference; contexts form retained lineage, with exactly one eligible active context. |
| CloneDecision | LogicalInstallation | Immutable result applying authority precedence to clone evidence; retains SAME, DISTINCT or UNKNOWN classification and activation consequence. |
| ActivationOutcome | LogicalInstallation | Immutable activation attempt/result linked to clone, compatibility, secret and provenance validation. |
| AuthoritativeDeclaration | LogicalInstallation | Protected declaration metadata/reference used at highest clone authority; secret/private content remains outside public export. |
| ProtectedProvenanceReference | LogicalInstallation | Integrity-checked external reference to protected lineage evidence, not a copy of protected material. |
| IdentityRegistration | CollisionRegistry | Retained association among installation context, reference kind, accepted opaque reference and private canonical-tuple handle/validation state; never deletes collision history. |
| EntityCurrentState | Entity | Exactly one mutable current state: ACTIVE, NOT_OBSERVED, UNAVAILABLE, REMOVED or IDENTITY_INVALID. HISTORICAL is excluded. |
| EntityLifecycleEvent | Entity | Immutable valid lifecycle transition with authoritative evidence/audit references. The ordered collection constitutes entity lifecycle history. |
| RelationshipCurrentState | Relationship | Exactly one mutable current tuple/status or explicit no-current-tuple projection under removal rules. |
| RelationshipLifecycleEvent | Relationship | Immutable create, replace, delete, recreate, continuity or discontinuity event. |
| ScanCapabilityOutcome | ScanRun | Normalized success/partial/unsupported/failure result for a collection capability; contributes to run completeness. |
| MigrationAttempt | MigrationState | Ordered immutable attempt/result; current in-progress coordination cannot be mistaken for successful version advancement. |

### 40.3 Value objects, reference objects and derived views

| Concept | Classification / owner | Canonical meaning |
|---|---|---|
| InstallationScope | Value object of InstallationContext | Accepted non-secret scope participating in CA-001 identity derivation; identity-affecting when changed. |
| SecretHandle | External-reference value of InstallationContext | Stable non-secret handle/generation metadata for protected secret storage; never secret bytes. |
| SourceReference | Value object used by Entity identity and Relationship endpoints | Exactly the accepted AI-002 public `source_ref` representation; installation-scoped and non-reversible. |
| TargetReference | Value object of RelationshipTuple | Exactly the frozen public `target_ref` representation and validation semantics; it is not redefined as an Entity or CA-001 `source_ref`. |
| RelationshipTuple | Value object of RelationshipCurrentState/event | Predicate plus accepted opaque endpoint references and continuity semantics. |
| LifecycleState | Value object of EntityCurrentState/event | Closed five-state current enum; HISTORICAL is a retention designation. |
| EvidenceReference | Reference object used by decisions/events/audit | Resolves to a retained normalized Observation, protected provenance reference or explicitly external authoritative reference. |
| PlatformEvidence | Observation role/kind, not a separate entity | Supporting evidence that may not independently determine clone identity. |
| ConcurrencyEvidence | Observation role/kind, not a separate entity | Evidence relevant to concurrent-clone classification; absence is not proof. |
| CompatibilityResult | Value object of CompatibilityDecision | Compatible, conditionally compatible, incompatible or unknown plus fail-closed capability result. |
| VersionVector | Value object of VersionState/CompatibilityDecision | Keeps architecture, public contract, implementation, DB schema, HASK knowledge and HUDD versions independent. |
| LifecycleHistory | Derived reference view, not persisted independently | Ordered EntityLifecycleEvent or RelationshipLifecycleEvent collection. It prevents a duplicate “history entity.” |
| CurrentInstallationProjection | Derived view | LogicalInstallation plus its eligible active InstallationContext and ActivationOutcome. |
| Diagnostic/ReportProjection | Derived view | Privacy-filtered reconstruction from operational roots; never an authority. |
| HASKKnowledgeReference | External reference | Identifies validated read-only HASK bundle knowledge/version without copying it into operational ownership. |
| HUDDKnowledgeReference | External reference | Identifies read-only HUDD knowledge/version without installation authority. |
| OperatorConfigurationReference | External reference | Identifies validated identity-relevant configuration owned outside the operational DB. |

`LifecycleHistory` was explicitly evaluated and is not an aggregate root or
owned persisted entity: its canonical records are lifecycle events. This avoids
duplicating history. InstallationContext is an owned entity, not a second
installation authority. CollisionRegistry is an aggregate root because its
installation-wide atomic uniqueness/history boundary is independent of any one
Entity.

## 41. Canonical identity ownership

| Concept | Internal identity | Public/stable identity | Natural/synthetic key semantics | Scope / external references |
|---|---|---|---|---|
| LogicalInstallation | Stable synthetic root identity | No public identity required | Synthetic authority; hardware, hostname, MAC and timestamps are prohibited natural identities | Owns context lineage; references protected provenance. |
| InstallationContext | Synthetic identity unique within LogicalInstallation | InstallationScope is public only where accepted architecture permits | Context/generation combination is a conceptual natural uniqueness rule, not a column design | SecretHandle points to external secret store. |
| CollisionRegistry | Synthetic root identity | None | One registry per LogicalInstallation is natural cardinality | Installation-scoped. |
| IdentityRegistration | Synthetic internal identity | CA-001-derived opaque reference; stable within accepted context/generation/format | Private canonical tuple + kind + context is natural identity input; never public | Belongs to registry; source_ref resolves through it. |
| Entity | Synthetic aggregate identity | Accepted opaque SourceReference | IdentityRegistration is authority; current Home Assistant raw entity ID is external/private evidence, not public authority | Exactly one LogicalInstallation through registry/context. |
| Relationship | Synthetic aggregate identity | Accepted relationship ID; source uses SourceReference and target uses TargetReference | Accepted `(predicate, source_ref, target_ref)` tuple/continuity semantics provide natural uniqueness | Source is installation-scoped; target obeys frozen validation and scope rules. |
| ScanRun | Synthetic request/run identity | Optional safe audit correlation only | Idempotency identity is stable after creation | Scoped to one LogicalInstallation/context. |
| Observation | Synthetic stable record identity | Only allowlisted projection IDs | Run + normalized observation identity semantics provide deduplication context | References one run and optionally one subject/evidence target. |
| CompatibilityDecision | Synthetic decision identity | Safe result may be exported, not identity | Version/context/request combination is decision input, not replacement identity | References VersionState/context/run as applicable. |
| AuditRecord | Synthetic immutable identity | Safe correlation may be exported | Idempotency/decision correlation prevents duplicate audit | References roots/events; never owns them. |
| VersionState | Singleton synthetic identity per DB | Version values may be public individually | Singleton cardinality, not a shared version namespace | References external HASK/HUDD versions without owning stores. |
| MigrationState | Singleton synthetic current identity plus attempt identities | Never public domain identity | Ordered attempt identity/history | Scoped to one operational DB. |

Canonical installation identity exists only on LogicalInstallation. Clone
continuity is represented only by CloneDecision and retained InstallationContext
lineage. Collision authority exists only in CollisionRegistry. `source_ref`
belongs as the public opaque identity value of an Entity registration and as a
Relationship endpoint reference; it is not owned by Observation, ScanRun, HUDD
or the HASK bundle.

## 42. Conceptual relationships and multiplicities

- One LogicalInstallation owns one or more InstallationContexts; at most one is
  eligible as the active context.
- One LogicalInstallation owns many CloneDecisions, ActivationOutcomes,
  AuthoritativeDeclarations and ProtectedProvenanceReferences.
- One LogicalInstallation has exactly one CollisionRegistry.
- One CollisionRegistry owns many IdentityRegistrations.
- One LogicalInstallation contains many Entities, Relationships, ScanRuns,
  CompatibilityDecisions and AuditRecords through installation-scoped
  references; these remain aggregate roots rather than owned entities.
- One Entity resolves through exactly one current accepted IdentityRegistration
  and owns exactly one EntityCurrentState plus many EntityLifecycleEvents.
- One Relationship owns one RelationshipCurrentState and many
  RelationshipLifecycleEvents, references exactly one source Entity through
  its SourceReference, and carries exactly one TargetReference for a binary
  tuple. The target is not assumed to be an Entity; it follows the frozen
  target-reference model. Source, target and tuple must satisfy the accepted
  scope and validation rules.
- One ScanRun owns one or more ScanCapabilityOutcomes and is the collection
  context for zero or many Observations.
- One Observation belongs to exactly one ScanRun and may reference zero or one
  primary subject aggregate. It may be referenced by many lifecycle events,
  decisions or audit records; those references do not transfer ownership.
- One CompatibilityDecision evaluates one VersionVector for one operational
  context and may govern zero or many ActivationOutcomes/capability boundaries.
- One AuditRecord describes exactly one governed decision or transition and may
  reference several evidence records and affected roots.
- One operational database has exactly one VersionState and one MigrationState.
- One MigrationState owns many ordered MigrationAttempts.
- LifecycleHistory is one ordered view per Entity or Relationship, composed of
  that root's lifecycle events; no second copy exists.

No conceptual relation permits cross-installation endpoint aliasing, secret
ownership by SQLite, or operational ownership of HASK/HUDD data.

## 43. Current state, history, observations and audit

| Concern | Canonical owner | Non-duplication rule |
|---|---|---|
| Current installation/context | LogicalInstallation / InstallationContext | Current projection references the latest valid decisions; it does not copy decision evidence. |
| Current entity lifecycle | EntityCurrentState | Exactly one row-equivalent concept; no HISTORICAL value. |
| Entity history | EntityLifecycleEvent collection | Append-only events; LifecycleHistory is only their ordered view. |
| Current relationship | RelationshipCurrentState | Exactly one current tuple/status projection. |
| Relationship history | RelationshipLifecycleEvent collection | Append-only create/change/removal events; no duplicate history store. |
| Collected normalized facts | Observation | Immutable classed fact linked to ScanRun; it is not current state unless a transaction derives/replaces a projection. |
| Compatibility history | CompatibilityDecision | Each evaluation is immutable; current capability projection references the applicable result. |
| Decision explanation | AuditRecord | Immutable envelope references observations/events/decisions without copying their canonical content. |
| Collision/identity history | IdentityRegistration under CollisionRegistry | Retained independently of current entity/relationship presence. |

A complete scan transaction may append Observations, replace current
projections, append lifecycle events and create AuditRecords together. A failed
or partial scan records only its run/outcomes and allowed observations/audit;
absence cannot mutate current projections. Read/report models join references
at query time and never become a second authority.

## 44. Bounded contexts

| Bounded context | Owned conceptual content | Explicit exclusions / connection |
|---|---|---|
| HASK operational database | All ten aggregate roots, their owned entities and persisted value/reference metadata from sections 40–43 | Excludes secret bytes, HASK/HUDD knowledge content, raw payloads, configuration bodies and report projections. |
| Protected secret storage | Installation-local CA-001 secret material and provider-managed integrity/access metadata | Operational DB holds only SecretHandle/generation validation metadata. |
| HASK provider/bundle | Authoritative YAML and validated generated read-only knowledge bundle | Connected by HASKKnowledgeReference; never written or made installation identity authority. |
| HUDD | Packaged read-only device knowledge and its independent schema/version | Connected by HUDDKnowledgeReference; never owns operational entity identity. |
| Operator configuration | Configuration and operator overrides in existing owners | Operational decisions retain only validated reference/version/evidence needed for audit. |
| Generated output/reports/API | Derived privacy-filtered projections | Rebuildable; never writes authority back to operational DB. |
| Disposable runtime/cache | Temporary K values and existing non-authoritative caches | May be lost; never recovery or identity source. |

## 45. Conceptual repository ownership

These are ownership names, not interfaces or implementation APIs.

| Conceptual repository owner | Owns exclusively | May reference but never own |
|---|---|---|
| LogicalInstallationRepository | LogicalInstallation, InstallationContexts, CloneDecisions, ActivationOutcomes, AuthoritativeDeclarations, ProtectedProvenanceReferences | Secret material, observations, compatibility/audit roots |
| CollisionRegistryRepository | CollisionRegistry and IdentityRegistrations | Entity/Relationship roots, secret bytes |
| EntityRepository | Entity, EntityCurrentState and EntityLifecycleEvents | IdentityRegistration, Observation, AuditRecord |
| RelationshipRepository | Relationship, RelationshipCurrentState and RelationshipLifecycleEvents | Endpoint Entities/registrations, Observation, AuditRecord |
| ScanRunRepository | ScanRun and ScanCapabilityOutcomes | Observations and affected domain roots |
| ObservationRepository | Observation roots | ScanRun, subject roots, protected evidence refs |
| CompatibilityDecisionRepository | CompatibilityDecision roots | VersionState, context, run, audit |
| AuditRepository | AuditRecord roots | All referenced evidence/decision/subject roots |
| VersionStateRepository | VersionState root | External HASK/HUDD version references |
| MigrationStateRepository | MigrationState and MigrationAttempts | VersionState and backup-validation references |

The DB-001B transaction service conceptually coordinates repository owners for
atomic cross-root work. Coordination does not change ownership or authorize an
interface design.

## 46. Aggregate consistency boundaries

| Aggregate | Creation / modification boundary | Deletion and history | Recovery boundary |
|---|---|---|---|
| LogicalInstallation | Created only from authoritative initialization; context/clone/activation changes are one governed installation decision | Root deletion prohibited while any identity/history exists; decisions/lineage preserved | Consistent DB + secret + provenance + identity configuration |
| CollisionRegistry | Created with LogicalInstallation; registration only through atomic collision check | Registry/history deletion prohibited for installation lifetime | Validated DB restore; unavailable/corrupt registry fails closed |
| Entity | Created after accepted identity registration; current state changes only with valid evidence/transition | Physical current projection may end, but identity and lifecycle history remain | Registry + lifecycle history + latest valid evidence |
| Relationship | Created after endpoint/reference validation; tuple changes only via continuity/recreation transaction | Current relation may be removed; events and referenced identity history remain | Endpoint registry plus relationship events |
| ScanRun | Created per attempt; only terminalization and owned capability outcomes modify it | Terminal run retained while referenced; running/interrupted never converted silently to complete | Recover interrupted as failed/non-complete |
| Observation | Created only after normalization/classification; immutable thereafter | Deletion follows sole DB-001C policy and is forbidden while referenced | Required A–F restored from validated backup; others regenerate/discard per policy |
| CompatibilityDecision | Created atomically from validated version inputs; immutable | Retain while activation/run/audit depends on it | Re-evaluation creates new decision; historical decision restored, not rewritten |
| AuditRecord | Created with governed transition/decision; immutable | Required audit cannot be deleted or overwritten | Validated immutable backup only |
| VersionState | Created with store initialization; changes only with compatibility/migration validation and audit | Singleton cannot be deleted during normal operation | Compatible implementation or governed migration/restore |
| MigrationState | Created with store; exclusive migration changes current status and appends attempts | Attempt history immutable; state deletion prohibited | Rollback transaction or restore pre-migration consistency unit |

## 47. Cross-cutting concept map

| Concern | Canonical conceptual location |
|---|---|
| Logical installation identity | LogicalInstallation root only; InstallationModel/ScanRun are never identity authorities |
| Installation scope and secret generation reference | InstallationContext with InstallationScope and external SecretHandle; secret bytes remain outside the DB |
| Collision uniqueness and retained history | CollisionRegistry with owned IdentityRegistrations |
| Stable public `source_ref` | SourceReference value authorized by IdentityRegistration and consumed by Entity/Relationship; never Observation ID or raw identifier |
| Version compatibility | VersionState + immutable CompatibilityDecision + referenced ActivationOutcome/AuditRecord |
| Clone continuity | LogicalInstallation-owned CloneDecision and InstallationContext lineage |
| Removal semantics | EntityCurrentState/EntityLifecycleEvent and RelationshipCurrentState/RelationshipLifecycleEvent |
| Relationship continuity | Relationship aggregate plus accepted SourceReference and frozen TargetReference; source identity resolves through CollisionRegistry |
| Relationship tuple | RelationshipCurrentState and RelationshipLifecycleEvent using exactly `(predicate, source_ref, target_ref)` semantics |
| Scan completeness and absence gate | ScanRun with owned ScanCapabilityOutcomes; only complete terminal authority may support absence transitions |
| Audit evidence | AuditRecord referring to Observation, decision, event and protected-provenance references |
| Compatibility decisions | CompatibilityDecision aggregate; never encoded only in VersionState current projection |
| Migration state | MigrationState/MigrationAttempt with VersionState update only after validation |
| Authoritative declaration | LogicalInstallation-owned protected AuthoritativeDeclaration metadata/reference |
| Protected provenance | LogicalInstallation-owned ProtectedProvenanceReference to external integrity-protected evidence |
| Platform/concurrency evidence | Typed Observation roles referenced by CloneDecision/AuditRecord; never independent identity authority |
| Activation outcome | LogicalInstallation-owned ActivationOutcome referencing clone, compatibility, secret and provenance validations |
| Domain-specific UNKNOWN/fail-closed outcomes | CloneDecision, CompatibilityDecision and ActivationOutcome retain their distinct closed result domains; no shared enum is inferred |
| HISTORICAL retention | Designation expressed by retained events/identity history, never EntityCurrentState |

Every accepted AI-002 concept has exactly one canonical owner or representation;
cross-cutting use is by reference, not duplicate ownership.

## 48. Canonical conceptual model diagram

```text
EXTERNAL / READ-ONLY CONTEXTS
┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐
│ HASK bundle      │  │ HUDD         │  │ Operator config    │
│ read-only        │  │ read-only    │  │ external owner     │
└────────┬─────────┘  └──────┬───────┘  └─────────┬──────────┘
         │ reference          │ reference          │ reference
         └────────────────────┼────────────────────┘
                              ▼
HADOCS-OWNED HASK OPERATIONAL SQLITE CONTEXT
┌───────────────────────────────────────────────────────────────────────┐
│ LogicalInstallation (aggregate root)                                 │
│  ├─ 1..* InstallationContext ── SecretHandle ───────────────┐        │
│  ├─ * CloneDecision / ActivationOutcome                    │        │
│  ├─ * AuthoritativeDeclaration / ProtectedProvenanceRef    │        │
│  └─ 1 CollisionRegistry (aggregate root)                   │        │
│       └─ * IdentityRegistration ── opaque SourceReference  │        │
│                                                              │        │
│  * Entity (aggregate root)                                    │        │
│     ├─ 1 EntityCurrentState                                   │        │
│     └─ * EntityLifecycleEvent ─┐                              │        │
│                                ├─ LifecycleHistory (view only)│        │
│  * Relationship (aggregate root)                              │        │
│     ├─ source Entity (1) / TargetReference (1)                │        │
│     ├─ 1 RelationshipCurrentState                             │        │
│     └─ * RelationshipLifecycleEvent ──────────────────────────┘        │
│                                                                        │
│  * ScanRun (aggregate root) ── * ScanCapabilityOutcome                │
│       └─ * Observation (independent immutable aggregate roots)         │
│              └─ referenced by lifecycle events/decisions/audit        │
│                                                                        │
│  * CompatibilityDecision ───────┐                                     │
│  * AuditRecord ─────────────────┼─ references, never owns other roots │
│  1 VersionState ────────────────┤                                     │
│  1 MigrationState ─ * MigrationAttempt                               │
└─────────────────────────────────┼─────────────────────────────────────┘
                                  │ non-secret handle / integrity refs
                                  ▼
                         ┌────────────────────┐
                         │ Protected secret   │
                         │ storage (external) │
                         └────────────────────┘

Generated reports/API = privacy-filtered reconstructable projections only.
```

## 49. DB-001D validation and next-batch gate

| Check | Result |
|---|---|
| Aggregate roots | PASS — 10 |
| Canonical persisted conceptual types | PASS — 10 roots + 12 owned entities; value/reference objects and views are separately classified |
| AI-002 concepts represented exactly once | PASS — section 47 canonical-location map |
| Duplicate conceptual persistence entities | NONE — LifecycleHistory and projections are views, platform/concurrency are Observation roles |
| Every conceptual entity has one owner | PASS — sections 40 and 45 |
| Every identity has one authority | PASS — section 41 |
| Current state/history/audit separated | PASS — section 43 |
| Conceptual relationship groups | PASS — 14 multiplicity rules in section 42 |
| Bounded contexts | PASS — 7 |
| New decisions | PASS — DB001-D-015 through DB001-D-020 (6) |
| HUDD separate and read-only | PASS |
| HASK bundle separate and read-only | PASS |
| Secret storage external | PASS |
| SQL, columns, SQL types or foreign keys defined | NO |
| Executable or physical schema defined | NO |
| Migration design/implementation created | NO |
| Repository interfaces defined | NO — ownership only |
| Code/tests/fixtures/dependencies/configuration changed | 0 |
| Contract `1.0.0` active; proposed `2.0.0` inactive | PASS |
| Implementation authorized or begun | NO |

Remaining work before DB-001 completion:

1. translate the conceptual model into a logical relational model with
   non-executable attributes, candidate keys and referential/normal-form rules;
2. allocate retention and invariant requirements to that logical model;
3. define physical SQLite schema design and indexing without implementation;
4. complete migration and repository/unit-of-work planning;
5. perform final cross-document consistency and implementation-readiness review.

Recommended next batch: **DB-001E — Logical relational model, candidate keys
and normalization**. It must remain documentation-only and must not create SQL,
executable schemas, migrations, repositories, tests, dependencies or runtime
configuration.

The DB-001D validation above remains preserved. DB-001E below consumes it
without reopening DB-001A–D.

## 50. DB-001E logical-model decisions

| ID | Decision | Reason | Consequences | Future revisit trigger |
|---|---|---|---|---|
| DB001-D-021 | The canonical logical model contains 22 entity relations matching DB-001D types one-to-one plus three ownership-neutral association relations. | Preserves one canonical relation per persisted conceptual entity while representing N:N evidence/subject references in 3NF. | No entity is split into competing authority relations; association rows never own endpoints. | A physical review proves a relation cannot preserve its aggregate boundary or normalization. |
| DB001-D-022 | Every relation has one synthetic primary candidate key; natural/idempotency candidates are alternate unique keys and never replace installation-scoped authority. | Stable internal joins must survive mutable external facts while duplicates remain structurally detectable. | Public refs, canonical tuples and idempotency identities receive scoped uniqueness without becoming universal internal keys. | A governed identity architecture changes canonical key authority. |
| DB001-D-023 | Minimum 3NF is mandatory; only current projections and singleton current-version/migration projections are intentional denormalizations over immutable history. | Eliminates update anomalies while retaining efficient authoritative current state. | Projection updates must commit atomically with their immutable events/audit. | Measured workload plus governed review justifies another projection. |
| DB001-D-024 | Structural invariants use candidate/foreign/check constraints; transition, clone, compatibility and completeness semantics remain transaction-service rules with audit. | Some accepted semantics cannot be inferred from row structure, but structurally enforceable rules must not rely only on application code. | Every constraint family has a named owner and fail-closed consequence. | Physical SQLite capabilities cannot provide an allocated structural guarantee. |
| DB001-D-025 | Schema bootstrap and evolution use eight dependency-ordered conceptual phases under DB001-D-008; each phase validates before version advancement. | Enables deterministic creation/migration without conflating schema and public contract versions. | No executable migration is authorized; rollback remains restore-first. | Physical design introduces a dependency cycle not resolvable by phase ordering. |
| DB001-D-026 | Research masterlists and external knowledge never seed the operational identity database directly; verified versioned imports belong to the HASK/HUDD read-only knowledge build boundary, and the operational DB retains only validated external-dataset references. | Masterlists are research seeds, not authoritative installation facts; preserves DB001-D-001/D-020 boundaries. | Runtime ingestion cannot promote unverified seed rows or mutate identity state. | A future governed bounded-context change authorizes an operational reference-data store. |

## 51. Canonical logical relation catalog

Names below are stable logical names, not executable table names. “Primary key”
and “alternate key” describe candidate semantics only. Every identity is scoped
as defined by DB-001D; no SQL type or column definition is implied.

### 51.1 Aggregate-root relations

| Logical relation | Purpose / owner | Logical attributes | Candidate keys and uniqueness | Nullability / lifecycle / retention |
|---|---|---|---|---|
| logical_installation | LogicalInstallationRepository; canonical installation root | Internal identity; creation/retirement state; creation authority; recovery-set identity; audit/version references | Primary: synthetic installation identity. Alternate: validated recovery-set identity when present. Exactly one root identity per logical installation. | Core identity/authority required; retirement metadata optional until retired. Root survives contexts and is installation-lifetime retained. |
| collision_registry | CollisionRegistryRepository; one installation-wide registry | Internal identity; owning installation reference; availability/integrity status; format context | Primary: synthetic registry identity. Alternate: owning installation reference (unique). | Owner and status required. Exactly one per installation; deletion prohibited. |
| entity | EntityRepository; one runtime entity identity | Internal identity; installation/context and identity-registration references; authority/status metadata | Primary: synthetic entity identity. Alternate: accepted identity-registration reference (unique within installation). | All identity refs required. Lifecycle is expressed by owned current/event relations; retained with collision/history. |
| relationship | RelationshipRepository; one relationship identity | Internal identity; installation reference; accepted relationship ID; predicate; source/target reference values; identity status | Primary: synthetic relationship identity. Alternates: accepted relationship ID scoped to installation; canonical `(installation, predicate, source_ref, target_ref)` tuple. | Tuple/identity required. Current/event lifecycle is owned separately; retained with relationship history. |
| scan_run | ScanRunRepository; one collection attempt | Internal run identity; installation/context; idempotency identity; start/terminal time; completeness/status; safe failure metadata; implementation/version context | Primary: synthetic run identity. Alternate: installation-scoped idempotency identity. | Start/status required; terminal time/failure metadata conditional on outcome. Running becomes exactly one terminal state. |
| observation | ObservationRepository; one normalized DB-001C classified fact | Internal identity; run reference; taxonomy class; authority/provenance; normalized payload descriptor; observed time; privacy/retention designation; optional primary-subject link indicator | Primary: synthetic observation identity. Alternate: run-scoped normalized observation identity/idempotency candidate. | Run/class/authority/time required; subject optional only for subjectless capability facts. Immutable; retention follows class. |
| compatibility_decision | CompatibilityDecisionRepository; one immutable evaluation | Internal identity; installation/context/run references as applicable; decision idempotency; independent version inputs; result; fail-closed outcome; decision time | Primary: synthetic decision identity. Alternate: context-scoped decision idempotency identity. | Context/version/result required; run optional for startup decisions. Immutable audit retention. |
| audit_record | AuditRepository; immutable decision envelope | Internal identity; installation; audit/idempotency identity; event kind/time; authority/provenance; architecture/contract/schema/implementation context; outcome/safe failure | Primary: synthetic audit identity. Alternate: installation-scoped audit idempotency identity. | Core context/outcome required; safe failure optional. Append-only and architecture-retained. |
| version_state | VersionStateRepository; current independent version vector | Internal singleton identity; DB schema, architecture, contract, implementation, HASK knowledge and HUDD version references; validation state | Primary: synthetic singleton identity. Alternate: operational-database singleton marker. | Each applicable dimension required; unavailable external versions represented explicitly, not null ambiguity. Current projection retained with audit. |
| migration_state | MigrationStateRepository; current migration coordinator | Internal singleton identity; current schema version; migration status; active attempt reference; validation/recovery-set state | Primary: synthetic singleton identity. Alternate: operational-database singleton marker. | Current version/status required; active attempt optional only when no migration is running. Singleton retained permanently. |

### 51.2 Owned-entity relations

| Logical relation | Purpose / owner | Logical attributes | Candidate keys and uniqueness | Nullability / lifecycle / retention |
|---|---|---|---|---|
| installation_context | LogicalInstallationRepository | Internal context identity; owner; InstallationScope; SecretHandle/generation metadata; lineage predecessor; eligibility/status; validity times | Primary: synthetic context identity. Alternate: owner-scoped `(scope, secret generation, CA-001 format)` context identity. | Owner/scope/secret reference/status required; predecessor optional for first context; retained lineage. |
| clone_decision | LogicalInstallationRepository | Internal decision identity; owner/context; request idempotency; evidence/authority references; classification; ambiguity/fail-closed outcome; time | Primary: synthetic decision identity. Alternate: installation-scoped decision idempotency identity. | Result/authority/time required; evidence refs conditional by accepted decision model. Immutable. |
| activation_outcome | LogicalInstallationRepository | Internal outcome identity; owner/context; request idempotency; clone/compatibility/secret/provenance validation refs; requested/result state; safe failure; time | Primary: synthetic outcome identity. Alternate: installation-scoped activation idempotency identity. | Required validation refs follow activation kind; safe failure optional. Immutable. |
| authoritative_declaration | LogicalInstallationRepository | Internal declaration identity; owner; declaration identity/version; protected content reference; authority/integrity status; validity interval | Primary: synthetic declaration identity. Alternate: owner-scoped declaration identity/version. | Protected reference/status required; end validity optional until superseded. Immutable versions retained. |
| protected_provenance_reference | LogicalInstallationRepository | Internal reference identity; owner/context; external provider reference; integrity/version/status metadata | Primary: synthetic reference identity. Alternate: owner-scoped provider reference/version. | External reference/integrity required; unavailable state explicit. Retained with lineage/audit. |
| identity_registration | CollisionRegistryRepository | Internal registration identity; registry/context; reference kind/format; private canonical-tuple handle; accepted opaque reference; generation; registration/retirement status; audit refs | Primary: synthetic registration identity. Alternates: registry-scoped private canonical tuple identity; registry-scoped opaque reference. | Identity inputs/results required; retirement optional until retired. Append-only history; no destructive deletion. |
| entity_current_state | EntityRepository | Internal state identity; owner entity; closed LifecycleState; effective time; source event/run refs; historical designation excluded | Primary: synthetic state identity. Alternate: owner entity reference (unique 1:1). | State/effective/source required. Replaced only atomically with event/audit; retained current projection. |
| entity_lifecycle_event | EntityRepository | Internal event identity; owner entity; transition idempotency; prior/result state; evidence/run/audit refs; event time/reason | Primary: synthetic event identity. Alternate: entity-scoped transition idempotency identity. | Prior state optional only for creation; result/evidence/time required. Immutable history. |
| relationship_current_state | RelationshipRepository | Internal state identity; owner relationship; current tuple/status; source event/run; effective time | Primary: synthetic state identity. Alternate: owner relationship reference (unique 1:1). | Explicit no-current-tuple status governs conditional tuple presence. Replaced atomically with event/audit. |
| relationship_lifecycle_event | RelationshipRepository | Internal event identity; owner relationship; transition idempotency; prior/result tuple/status; continuity classification; evidence/run/audit refs; time | Primary: synthetic event identity. Alternate: relationship-scoped transition idempotency identity. | Prior tuple optional for creation; result may explicitly represent deletion. Immutable history. |
| scan_capability_outcome | ScanRunRepository | Internal outcome identity; owner run; capability identity; status; retryability; safe error; observation/completeness contribution | Primary: synthetic outcome identity. Alternate: `(run, capability identity)` unique. | Status required; retry/error conditional. Immutable after run terminalization. |
| migration_attempt | MigrationStateRepository | Internal attempt identity; owner state; ordered migration identity; from/to version; start/end/status; recovery-set validation; safe failure/audit refs | Primary: synthetic attempt identity. Alternates: ordered migration identity per operational DB; migration execution idempotency identity. | Start/from/to/status required; end/failure conditional. Immutable when terminal. |

### 51.3 Association relations

| Logical relation | Purpose / ownership | Logical attributes | Candidate keys / nullability / retention |
|---|---|---|---|
| observation_subject_link | Ownership-neutral reference from Observation to one subject root | Observation reference; subject kind; subject internal reference; role | Primary candidate: synthetic link identity. Alternate: `(observation, role)` unique. All values required. Deleted only when observation may be deleted; never cascades to subject. |
| audit_evidence_link | N:N association between AuditRecord and retained evidence Observation | Audit reference; observation reference; evidence role/order | Primary candidate: synthetic link identity. Alternate: `(audit, observation, role)` unique. Required and immutable with audit. |
| audit_subject_link | N:N association from AuditRecord to affected aggregate/event identities | Audit reference; subject kind; subject internal reference; role | Primary candidate: synthetic link identity. Alternate: `(audit, subject kind, subject reference, role)` unique. Required and immutable with audit. |

The tagged subject links are intentional reference relations because one
Observation/AuditRecord may refer to different aggregate kinds. Their tagged
reference integrity is owned by the transaction service plus relation-specific
validation; they do not create polymorphic ownership or cascade deletion.

## 52. Candidate-key strategy and counts

- All **25 logical relations** have one synthetic primary candidate key.
- The catalog defines **28 alternate candidate keys**: scoped natural,
  singleton, canonical-tuple or idempotency candidates. None is globally unique
  unless its row explicitly says so.
- Synthetic keys are internal, opaque and immutable. They carry no hardware,
  hostname, MAC, timestamp or secret semantics.
- Public opaque references remain alternate domain identities, never SQLite row
  identities.
- Idempotency keys are scoped to their aggregate/installation/run boundary and
  make retries return the existing semantic result or reject a conflicting
  payload.
- Natural candidates containing private canonical identity inputs are validated
  through the collision boundary and never exported.
- A null or missing component cannot satisfy a candidate key. Conditional data
  is excluded from the key or represented by an explicit closed status.

Physical design may implement a candidate with a unique constraint or unique
index, but DB-001E does not choose syntax.

## 53. Relationship mapping

| Relationship | Multiplicity | Owner / reference direction | Cascade and history expectation |
|---|---|---|---|
| LogicalInstallation → InstallationContext | 1:N | Installation owns contexts; context references owner | No delete cascade after identity use; lineage retained. |
| LogicalInstallation → CloneDecision | 1:N | Installation owns decisions | Append-only; installation retirement retains decisions. |
| LogicalInstallation → ActivationOutcome | 1:N | Installation owns outcomes | Append-only; no cascade deletion. |
| LogicalInstallation → AuthoritativeDeclaration | 1:N | Installation owns declaration versions | Supersession retains prior versions. |
| LogicalInstallation → ProtectedProvenanceReference | 1:N | Installation owns protected refs | No cascade to external provider; references retained. |
| LogicalInstallation → CollisionRegistry | 1:1 | Registry references installation | Delete prohibited; recovery unit shared. |
| CollisionRegistry → IdentityRegistration | 1:N | Registry owns registrations | Append-only history; no removal cascade. |
| InstallationContext → IdentityRegistration | 1:N | Registration references derivation context | Context retirement retains registrations. |
| IdentityRegistration → Entity | 1:0..1 current authority | Entity references accepted registration | Registration retained after entity removal. |
| LogicalInstallation → Entity | 1:N | Entity references installation/context authority | Installation cannot be deleted while entity/history exists. |
| Entity → EntityCurrentState | 1:1 | Entity owns current projection | Replace current projection, never cascade history. |
| Entity → EntityLifecycleEvent | 1:N | Entity owns events | Append-only; retained after current removal. |
| LogicalInstallation → Relationship | 1:N | Relationship references installation | No cascade that removes history. |
| Entity → Relationship source | 1:N | Relationship references one source Entity/SourceReference | Entity removal does not erase relationship history. |
| Relationship → RelationshipCurrentState | 1:1 | Relationship owns current projection | Replace only with event/audit transaction. |
| Relationship → RelationshipLifecycleEvent | 1:N | Relationship owns events | Append-only. |
| LogicalInstallation → ScanRun | 1:N | Run references installation/context | Terminal runs retained while referenced. |
| ScanRun → ScanCapabilityOutcome | 1:N | Run owns outcomes | Terminalization freezes outcomes. |
| ScanRun → Observation | 1:N | Observation references run; remains independent root | Run deletion prohibited while mandatory observations exist. |
| Observation → subject aggregate | 0..1:N through observation_subject_link | Link references both; owns neither | Link follows observation retention, never subject cascade. |
| AuditRecord ↔ Observation | N:N through audit_evidence_link | Link is ownership-neutral | Link immutable; endpoints cannot be deleted while mandatory link exists. |
| AuditRecord ↔ affected subject | N:N through audit_subject_link | Link is ownership-neutral | Link immutable; no subject cascade. |
| VersionState → CompatibilityDecision | 1:N conceptual revision context | Decision references version snapshot values/current root context | Later VersionState changes do not rewrite decisions. |
| CompatibilityDecision → ActivationOutcome | 1:N | Outcome references applicable decision | Decision retained while outcome exists. |
| MigrationState → MigrationAttempt | 1:N | MigrationState owns attempts | Append-only terminal attempts. |
| MigrationState → VersionState | 1:1 coordination | Successful migration advances VersionState only after validation | Failure leaves prior version and records attempt. |

All cascades are conceptual. Required history, collision identity and audit use
restrict/retain semantics; only disposable association/current-projection rows
may follow an explicitly validated owner operation.

## 54. Normalization model

The logical model targets **minimum Third Normal Form**:

- every non-key fact depends on the whole candidate key of its relation;
- mutable facts are separated from immutable events/decisions;
- repeating evidence and subject references use association relations;
- independent version dimensions remain attributes of VersionState/value
  snapshots rather than encoded into unrelated identities;
- external HASK/HUDD/config/secret content is referenced, not copied;
- lifecycle enums, predicates, capability identities and taxonomy/retention
  classes are governed closed value sets, not mutable lookup authority tables.

Relation roles:

| Role | Relations |
|---|---|
| Current projection | entity_current_state, relationship_current_state, version_state, migration_state |
| Immutable history | identity_registration, entity_lifecycle_event, relationship_lifecycle_event, migration_attempt |
| Immutable decision/audit | clone_decision, activation_outcome, compatibility_decision, audit_record |
| Observation/run | scan_run, scan_capability_outcome, observation |
| Reference/association | protected_provenance_reference, observation_subject_link, audit_evidence_link, audit_subject_link |
| Configuration relation | None; configuration remains an external bounded context |
| Lookup relation | None initially; closed architecture enums are validated values |
| Seed/reference-data relation | None in operational DB; HASK/HUDD remain external read-only contexts |

Intentional denormalizations are limited to:

1. entity_current_state as the authoritative current projection over entity
   lifecycle events;
2. relationship_current_state as the current projection over relationship
   lifecycle events;
3. version_state as current version projection over compatibility/migration
   audit; and
4. migration_state as current coordinator projection over migration attempts.

Each projection is justified by current-state lookup and transaction gating.
It must update atomically with its immutable source event/audit; it cannot be
treated as historical authority by itself. Counts, report fields and health
values are not denormalized into the canonical model.

## 55. Logical constraint registry

| ID | Constraint | Primary owner | Failure behavior |
|---|---|---|---|
| LC-001 | One CollisionRegistry per LogicalInstallation | Database uniqueness | Reject duplicate registry. |
| LC-002 | At most one eligible active InstallationContext per LogicalInstallation | LogicalInstallation transaction | Roll back activation; preserve prior context. |
| LC-003 | SecretHandle/generation must validate before context activation | Secret boundary | Fail closed; no identity write. |
| LC-004 | Context lineage cannot cycle or cross LogicalInstallation | Transaction + referential validation | Reject context change. |
| LC-005 | Private canonical tuple unique within registry/kind/context | Database uniqueness | Roll back collision registration. |
| LC-006 | Opaque reference unique within registry/format/kind/context | Database uniqueness | Fail closed as collision. |
| LC-007 | IdentityRegistration history cannot be deleted after acceptance | Database append-only protection | Reject delete/purge. |
| LC-008 | Entity has exactly one accepted identity registration and installation | Referential constraint | Reject orphan/cross-scope entity. |
| LC-009 | One EntityCurrentState per Entity | Database uniqueness | Reject duplicate projection. |
| LC-010 | Entity current state is one closed five-state value; HISTORICAL excluded | Check constraint | Reject invalid state. |
| LC-011 | Entity transition follows accepted closed transition rules | Entity transaction | Roll back transition; retain prior state. |
| LC-012 | Relationship public ID and canonical tuple are installation-scoped unique | Database uniqueness | Reject duplicate/conflicting relationship. |
| LC-013 | Relationship source_ref resolves to the accepted source Entity registration | Referential + transaction validation | Reject relationship write. |
| LC-014 | target_ref satisfies frozen validation; no Entity assumption is added | Application/transaction validation | Reject malformed/unsupported target. |
| LC-015 | One RelationshipCurrentState per Relationship | Database uniqueness | Reject duplicate projection. |
| LC-016 | Relationship transition/recreation follows continuity rules | Relationship transaction | Roll back ambiguous mutation. |
| LC-017 | Run idempotency identity unique within LogicalInstallation | Database uniqueness | Return matching run or reject conflict. |
| LC-018 | ScanRun has one terminal outcome and cannot return to running | Check + transaction validation | Reject terminal rewrite. |
| LC-019 | Absence transitions require a complete terminal ScanRun | Scan transaction | Preserve current state on failed/partial run. |
| LC-020 | One ScanCapabilityOutcome per run/capability | Database uniqueness | Idempotent retry or reject conflict. |
| LC-021 | Observation taxonomy and retention values are closed and mutually consistent | Check + application validation | Reject persistence candidate. |
| LC-022 | Raw/secret data cannot enter normalized observation/audit payload | Secret/privacy boundary | Reject and emit safe failure only. |
| LC-023 | Immutable observations/events/decisions/audit cannot be updated | Database append-only protection | Reject mutation. |
| LC-024 | Association links reference existing allowed endpoints and transfer no ownership | Referential + transaction validation | Reject dangling/tag mismatch. |
| LC-025 | Audit idempotency identity unique and every governed transition has audit | Audit transaction + uniqueness | Roll back transition without audit. |
| LC-026 | Compatibility result belongs to a closed result domain and fail-closed outcome | Check + compatibility transaction | Reject/disable incompatible capability. |
| LC-027 | Version dimensions remain independent and schema forward versions are rejected | Migration validation | Refuse startup/write. |
| LC-028 | Migration attempts are ordered, exclusive and advance version only after validation | Migration transaction | Roll back or retain incomplete blocking state. |
| LC-029 | Required retained A–F records cannot be purged while referenced/required | Retention transaction | Reject purge. |
| LC-030 | Cross-installation references/aliases are prohibited | Transaction + scoped uniqueness | Fail closed; publish nothing. |

The database owns structural uniqueness, referential and closed-value rules;
aggregate transaction owners enforce semantic transitions; secret/privacy and
migration boundaries retain their DB-001B allocation. No constraint is left
without an owner.

## 56. Non-executable SQLite mapping expectations

The expected physical relation set is the 25 logical relations in section 51.
This is a mapping checklist, not a schema.

### Expected key and constraint mapping

- one primary-key mechanism per relation;
- unique enforcement for every alternate candidate key;
- foreign-key enforcement for fixed-kind owner/reference directions;
- closed-value checks for lifecycle, run, compatibility, taxonomy, retention,
  migration and activation domains;
- conditional-presence checks for terminal/failure/current-tuple semantics;
- append-only protection for identity registrations, lifecycle events,
  immutable decisions, audit records and terminal migration attempts;
- no generated identity derived from mutable or hardware values;
- generated values, if used physically, are limited to deterministic
  non-authoritative convenience values and never replace application-supplied
  accepted identity/audit semantics.

### Conceptual index families

In addition to primary/alternate candidate-key uniqueness, physical design is
expected to evaluate these **18 secondary index families**:

1. contexts by installation and lineage/status;
2. identity registrations by registry/context/kind/status;
3. entities by installation/context/current identity status;
4. entity current state by lifecycle value/effective time;
5. entity events by entity and event time/order;
6. relationships by installation/predicate/source_ref/target_ref;
7. relationship current state by status/effective time;
8. relationship events by relationship and event time/order;
9. runs by installation/context/start/terminal status;
10. capability outcomes by run/status;
11. observations by run/class/time;
12. observation subjects by subject kind/reference;
13. compatibility decisions by context/result/time;
14. audit records by installation/kind/time;
15. audit evidence links by observation;
16. audit subject links by subject kind/reference;
17. migration attempts by ordered identity/status/time; and
18. external knowledge/version references by source/version/validation status.

Index inclusion is conditional on query/workload verification in physical
design. Redundant indexes must be removed where a candidate-key index already
covers the same access prefix. Raw identifiers, secret material and unrestricted
payload text are never indexed.

## 57. Conceptual migration and bootstrap order

DB001-D-008 remains authoritative. Initial logical bootstrap/migration order has
eight dependency phases:

1. **Schema governance:** migration_state, migration_attempt and initial
   schema-version validation boundary.
2. **Version foundation:** version_state and independent version dimensions.
3. **Installation foundation:** logical_installation, installation_context,
   authoritative_declaration and protected_provenance_reference.
4. **Identity foundation:** collision_registry and identity_registration.
5. **Operational subjects:** entity, entity_current_state, relationship and
   relationship_current_state.
6. **Collection facts:** scan_run, scan_capability_outcome, observation and
   observation_subject_link.
7. **History and decisions:** entity_lifecycle_event,
   relationship_lifecycle_event, clone_decision, compatibility_decision and
   activation_outcome.
8. **Audit closure:** audit_record, audit_evidence_link, audit_subject_link,
   invariant validation and only then activation eligibility.

Future migrations are ordered, transactional where supported, exclusive-writer
operations. They declare from/to schema versions, validate preconditions,
preserve required history, write an immutable MigrationAttempt/AuditRecord and
advance VersionState only after post-validation. Forward-unknown versions are
rejected. Rollback is transaction rollback before commit or restore of the
validated pre-migration recovery set afterward; automatic down-migration is
prohibited. Contract `1.0.0` remains independent and active.

## 58. Unit-of-work boundaries

| Unit of work | Aggregate owners coordinated | Atomic logical effects | Failure/idempotency |
|---|---|---|---|
| Installation bootstrap/activation | LogicalInstallation, CollisionRegistry, VersionState, CompatibilityDecision, Audit | Validate external secret/provenance; create/activate context; record decisions/audit together | No activation on mismatch; request idempotency returns same outcome or rejects conflict. |
| Collision registration/entity creation | CollisionRegistry, Entity, Audit | Check/register identity, create Entity/current state and audit as one unit | No public identity/entity without collision commit; scoped canonical idempotency. |
| Complete scan | ScanRun, Observation, Entity, Relationship, Audit | Terminalize complete run; persist allowed observations; update projections; append events/audit | Whole unit commits or rolls back; scan idempotency prevents duplicate transition. |
| Partial/failed scan | ScanRun, Observation where allowed, Audit | Terminalize non-complete outcome and safe evidence only | Never performs absence-derived state/removal changes. |
| Entity lifecycle/removal | Entity, Observation, Audit | Validate evidence; replace current state; append lifecycle event/audit | Invalid transition preserves prior current state; transition idempotency. |
| Relationship create/replace/remove/recreate | Relationship, Entity reference, Observation, Audit | Validate source/target/tuple; replace projection; append event/audit | No ambiguous mutation or history deletion; tuple/transition idempotency. |
| Clone classification/context transition | LogicalInstallation, CollisionRegistry reference, Observation, CompatibilityDecision, Audit | Apply precedence; preserve or create context as authorized; record classification/activation | UNKNOWN fails closed; never regenerates secret automatically. |
| Compatibility decision | CompatibilityDecision, VersionState reference, Audit | Persist version inputs/result/audit and capability boundary | Incompatible/unknown follow accepted closed result; decision idempotency. |
| Migration | MigrationState, VersionState, all affected owners, Audit | Exclusive ordered transformation, validation, attempt/audit and version advance | Failure rolls back or blocks with incomplete state; restore-first recovery. |
| Retention/purge | Relevant owner, association links, Audit | Prove policy/reference eligibility, remove only allowed G/J/L or superseded projections, record audit when material | Any required A–F dependency rejects whole purge. |

These units refine DB-001B section 22; they do not define service/repository
interfaces or implementation APIs.

## 59. Seed-data readiness and external knowledge boundary

Research masterlists are **research seeds**, never authoritative operational
rows. They do not enter the 25-relation HASK operational model.

The future seed pipeline belongs to the existing HASK/HUDD offline knowledge
build contexts:

- **ownership:** HASK owns verified knowledge records/bundles; HUDD owns its
  independent curated device dataset; the masterlist owns neither authority;
- **import boundary:** offline build/curation only, never scan transaction or
  runtime writer;
- **versioning:** each produced dataset has a stable dataset identity, content
  version/checksum, source/provenance set, schema version and verification state;
- **idempotency:** reimport of identical dataset identity/version/checksum yields
  identical output or a no-op; changed content requires a new version;
- **duplicate detection:** stable normalized seed/source identifiers detect
  duplicates; conflicts remain explicit and cannot be silently merged;
- **update behavior:** verified records are additive/superseding according to
  their own knowledge governance; previous released datasets remain auditable;
- **history:** import/build manifests and verification outcomes are retained in
  the provider context, not copied into operational identity audit;
- **verification:** only validated generated HASK bundle/HUDD artifacts may be
  referenced by VersionState/HASKKnowledgeReference/HUDDKnowledgeReference;
  unverified masterlist rows remain seed-only;
- **runtime behavior:** operational database stores only the validated external
  artifact identity/version/checksum/status reference needed for reproducibility.

No importer, seed table, seed migration or direct research-to-runtime promotion
is authorized by DB-001E.

## 60. DB-001E validation and next-batch gate

| Check | Result |
|---|---|
| Conceptual entity types mapped one-to-one | PASS — 22 entity relations for 10 roots + 12 owned entities |
| Ownership-neutral association relations | PASS — 3 |
| Total logical relations | 25 |
| Every relation has a primary candidate key | PASS — 25 |
| Alternate candidate keys | 28 scoped candidates |
| Minimum normalization | PASS — 3NF plus 4 documented current projections |
| Constraint ownership | PASS — 30 named constraints |
| History authority | PASS — one owner per history; views do not duplicate it |
| Relationship mappings | PASS — 26 |
| Secondary conceptual index families | 18, subject to physical workload review |
| Migration/bootstrap phases | 8 |
| Unit-of-work boundaries | 10 |
| Seed data respects bounded contexts | PASS |
| Raw masterlist rows enter operational identity DB | NO |
| Executable SQL or table-creation statement introduced | NO |
| Executable schema/migration created | NO |
| Repository interface or implementation created | NO |
| Code/tests/fixtures/dependencies/configuration changed | 0 |
| Contract `1.0.0` remains active; proposed `2.0.0` inactive | PASS |
| Implementation authorized or begun | NO |

The logical model is ready for documentation-only physical SQLite design.

Remaining work before DB-001 completion:

1. DB-001F physical SQLite schema, concrete column/type/null/default/index/check
   and append-only enforcement design—still non-executable unless authority is
   expanded;
2. final migration/repository/unit-of-work implementation plan aligned to that
   physical design;
3. complete consistency, traceability, recovery and implementation-readiness
   review; and
4. DB-001 close-out under governance, without authorizing implementation.

Recommended next batch: **DB-001F — Physical SQLite schema and enforcement
design (documentation only)**. It may specify concrete physical design but must
not create executable SQL, migrations, dependencies, repositories, tests or
runtime configuration unless a future authority explicitly permits them.

The DB-001E validation above remains preserved. DB-001F below consumes it
without reopening DB-001A–E.

## 61. DB-001F physical-design decisions

| ID | Decision | Reason | Consequences | Future revisit trigger |
|---|---|---|---|---|
| DB001-D-027 | Each of the 25 logical relations maps one-to-one to the identically named snake_case SQLite table and the closed column catalogue in section 63. | Eliminates naming translation and makes physical coverage mechanically reviewable. | No catalogue/seed tables are added; lifecycle/audit boundaries remain physical. | A governed logical-model revision changes a relation. |
| DB001-D-028 | Internal synthetic identities use engine-assigned positive INTEGER primary keys; public/domain identities and idempotency keys use canonical TEXT; SHA-256 digests use 32-octet BLOB; timestamps use canonical UTC TEXT; schema versions use non-negative INTEGER. | Fits SQLite row identity/index locality while preserving frozen public reference bytes and version independence. | INTEGER keys are never exported as domain identity; `source_ref`/`target_ref` semantics are unchanged. | Portability review requires globally mergeable internal keys or a different engine. |
| DB001-D-029 | Fixed references use foreign keys with restrictive deletion; structural closed sets/checks and scoped uniqueness are database-enforced; append-only tables use triggers; semantic transitions remain transaction-enforced. | Maximizes structural enforcement without pretending SQLite can decide clone/continuity/completeness semantics. | Constraint failures are stable recoverable categories for future repositories. | SQLite cannot enforce a required invariant under the accepted writer model. |
| DB001-D-030 | The initial schema has 18 mandatory named secondary indexes in addition to primary/alternate-key enforcement; redundant speculative indexes are prohibited. | Every index traces to DB-001E workload/invariant evidence. | Physical review must prove prefix overlap before removing one; later additions require workload evidence. | Measured query plans show an index harmful/redundant or a bounded query unmet. |
| DB001-D-031 | SQLite runs with foreign keys enabled, WAL, synchronous FULL, trusted schema disabled, recursive triggers enabled, in-memory temp storage, 5-second busy timeout and serialized IMMEDIATE writes; application_id is `0x4841534B`. | Aligns durability, local/offline operation, append-only enforcement and the single-writer architecture. | Startup validates settings; failure prevents operational activation. | A supported platform cannot provide a required setting or workload crosses the escalation gate. |
| DB001-D-032 | Physical bootstrap follows the eight DB-001E phases with authoritative schema state in version_state/migration_state and supplementary mirrored `user_version`. | Keeps dependency order deterministic and schema version separate from contract 1.0.0. | Migration files remain future work; incomplete/checksum-invalid state fails closed. | A future physical dependency requires an approved reordered migration plan. |

## 62. Physical conventions and column notation

This section makes the compact catalogue complete without executable SQL.

### Naming and storage

- Tables/columns/indexes/constraints use lowercase `snake_case` ASCII.
- `INTEGER` stores positive internal keys, booleans as checked `0/1`, ordinal
  values and non-negative schema/generation numbers.
- `REAL` is not required by the initial canonical model.
- `TEXT` stores normalized enums, canonical UTC RFC 3339 timestamps, UUID-form
  idempotency keys, opaque references, versions and canonical privacy-minimized
  JSON where explicitly named `_json`.
- `BLOB` stores exactly 32-octet SHA-256 digests/checksums. It never stores the
  CA-001 secret or raw payload.
- `NULL` is permitted only where a catalogue token carries `?`; absence never
  substitutes for an explicit closed UNKNOWN/unavailable state.

### Token legend

Every column token below has the form
`name:storage/null/source/mutability/privacy/export/retention/roles`.

- null: `N` = NOT NULL, `?` = nullable;
- source: `G` = SQLite-generated, `S` = supplied/validated, `D` = deterministic
  generated convenience value;
- mutability: `I` immutable, `C` controlled current projection, `T` terminalized
  once, `V` versioned by superseding row;
- privacy: `PUB` public, `PSN` public pseudonymous, `INT` internal, `PRV`
  protected reference/metadata;
- export: `E` allowlist exportable, `R` redacted/summarized only, `X` never;
- retention: `RC` current, `RH` mandatory history/audit, `RP` retained identity,
  `RG` configurable diagnostic;
- roles: `PK`, `AK`, `NK`, `FK→table`, `CHK`, `DIGEST`; omitted means ordinary
  non-key attribute. Defaults are prohibited unless the token says `DEF(value)`.

All PKs are `INTEGER/N/G/I/INT/X` and positive. All supplied IDs/refs are
validated before write. A table mutability class below applies to every column
unless a token explicitly says `C` or `T`. Secret bytes and raw identifiers have
no physical column.

## 63. Physical table and complete column catalogue

### 63.1 Aggregate-root tables

| Table / owner / role | Lifecycle, retention, recovery | Complete columns |
|---|---|---|
| logical_installation / LogicalInstallationRepository / current root | Restricted mutable; RP; recovery-set restore | `id:INTEGER/N/G/I/INT/X/RP/PK`; `state:TEXT/N/S/C/INT/R/RP/CHK`; `created_at:TEXT/N/S/I/INT/R/RP`; `retired_at:TEXT/?/S/C/INT/R/RP`; `creation_authority:TEXT/N/S/I/PRV/R/RP`; `recovery_set_ref:TEXT/N/S/I/PRV/X/RP/AK`; `current_context_id:INTEGER/?/S/C/INT/X/RP/FK→installation_context` |
| collision_registry / CollisionRegistryRepository / retained identity | Restricted mutable status; RP; loss fails closed | `id:INTEGER/N/G/I/INT/X/RP/PK`; `installation_id:INTEGER/N/S/I/INT/X/RP/FK→logical_installation,AK`; `integrity_status:TEXT/N/S/C/INT/R/RP/CHK`; `availability_status:TEXT/N/S/C/INT/R/RP/CHK`; `format_version:INTEGER/N/S/I/INT/R/RP/CHK`; `created_at:TEXT/N/S/I/INT/R/RP` |
| entity / EntityRepository / identity root | Restricted mutable status; RP; registry/history recovery | `id:INTEGER/N/G/I/INT/X/RP/PK`; `installation_id:INTEGER/N/S/I/INT/X/RP/FK→logical_installation`; `context_id:INTEGER/N/S/I/INT/X/RP/FK→installation_context`; `identity_registration_id:INTEGER/N/S/I/INT/X/RP/FK→identity_registration,AK`; `identity_status:TEXT/N/S/C/INT/R/RP/CHK`; `created_at:TEXT/N/S/I/INT/R/RP` |
| relationship / RelationshipRepository / identity root | Restricted mutable identity status; RP/RH | `id:INTEGER/N/G/I/INT/X/RP/PK`; `installation_id:INTEGER/N/S/I/INT/X/RP/FK→logical_installation`; `public_relationship_id:TEXT/N/S/I/PSN/E/RP/AK`; `predicate:TEXT/N/S/I/PUB/E/RP/NK`; `source_entity_id:INTEGER/N/S/I/INT/X/RP/FK→entity`; `source_ref:TEXT/N/S/I/PSN/E/RP/NK`; `target_ref:TEXT/N/S/I/PSN/E/RP/NK`; `identity_status:TEXT/N/S/C/INT/R/RP/CHK`; `created_at:TEXT/N/S/I/INT/R/RP` |
| scan_run / ScanRunRepository / run envelope | Mutable until terminal; RH by dependency | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `context_id:INTEGER/N/S/I/INT/X/RH/FK→installation_context`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `started_at:TEXT/N/S/I/INT/R/RH`; `terminal_at:TEXT/?/S/T/INT/R/RH`; `status:TEXT/N/S/T/INT/E/RH/CHK`; `completeness:TEXT/N/S/T/INT/E/RH/CHK`; `safe_error_code:TEXT/?/S/T/INT/R/RH`; `implementation_version:TEXT/N/S/I/INT/E/RH`; `contract_version:TEXT/N/S/I/PUB/E/RH` |
| observation / ObservationRepository / immutable fact | Immutable; DB-001C policy; restore A–F | `id:INTEGER/N/G/I/INT/X/RH/PK`; `scan_run_id:INTEGER/N/S/I/INT/X/RH/FK→scan_run`; `observation_key:TEXT/N/S/I/INT/X/RH/AK`; `taxonomy_class:TEXT/N/S/I/INT/E/RH/CHK`; `authority_class:TEXT/N/S/I/INT/R/RH/CHK`; `provenance_ref:TEXT/?/S/I/PRV/X/RH`; `observed_at:TEXT/N/S/I/INT/R/RH`; `normalized_payload_json:TEXT/N/S/I/INT/R/RH/CHK`; `privacy_class:TEXT/N/S/I/INT/R/RH/CHK`; `retention_policy:TEXT/N/S/I/INT/R/RH/CHK`; `immutable_digest:BLOB/N/D/I/INT/X/RH/DIGEST`; `created_at:TEXT/N/S/I/INT/R/RH` |
| compatibility_decision / CompatibilityDecisionRepository / immutable decision | Immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `context_id:INTEGER/?/S/I/INT/X/RH/FK→installation_context`; `scan_run_id:INTEGER/?/S/I/INT/X/RH/FK→scan_run`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `version_vector_json:TEXT/N/S/I/INT/R/RH/CHK`; `result:TEXT/N/S/I/INT/E/RH/CHK`; `capability_outcome:TEXT/N/S/I/INT/E/RH/CHK`; `decided_at:TEXT/N/S/I/INT/R/RH`; `decision_digest:BLOB/N/D/I/INT/X/RH/DIGEST`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record`; `safe_failure_code:TEXT/?/S/I/INT/R/RH` |
| audit_record / AuditRepository / immutable audit | Append-only immutable; RH; backup only | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `event_kind:TEXT/N/S/I/INT/R/RH/CHK`; `recorded_at:TEXT/N/S/I/INT/R/RH`; `authority:TEXT/N/S/I/PRV/R/RH`; `provenance_ref:TEXT/?/S/I/PRV/X/RH`; `architecture_version:TEXT/N/S/I/PUB/E/RH`; `contract_version:TEXT/N/S/I/PUB/E/RH`; `schema_version:INTEGER/N/S/I/INT/E/RH/CHK`; `implementation_version:TEXT/N/S/I/INT/E/RH`; `outcome:TEXT/N/S/I/INT/R/RH/CHK`; `safe_failure_code:TEXT/?/S/I/INT/R/RH` |
| version_state / VersionStateRepository / current singleton | Controlled current projection; RP; migration recovery | `id:INTEGER/N/G/I/INT/X/RP/PK`; `singleton_key:INTEGER/N/S/I/INT/X/RP/AK,CHK,DEF(1)`; `schema_version:INTEGER/N/S/C/INT/E/RP/CHK`; `architecture_version:TEXT/N/S/C/PUB/E/RP`; `contract_version:TEXT/N/S/C/PUB/E/RP`; `implementation_version:TEXT/N/S/C/INT/E/RP`; `hask_bundle_ref:TEXT/N/S/C/INT/R/RP`; `hask_bundle_version:TEXT/N/S/C/PUB/E/RP`; `hask_bundle_digest:BLOB/N/S/C/INT/X/RP/DIGEST`; `hask_compatibility_status:TEXT/N/S/C/INT/E/RP/CHK`; `hask_activated_at:TEXT/?/S/C/INT/R/RP`; `previous_hask_bundle_ref:TEXT/?/S/C/INT/R/RP`; `rollback_hask_bundle_ref:TEXT/?/S/C/INT/R/RP`; `hudd_ref:TEXT/N/S/C/INT/R/RP`; `validation_status:TEXT/N/S/C/INT/R/RP/CHK` |
| migration_state / MigrationStateRepository / current singleton | Controlled current coordinator; RP | `id:INTEGER/N/G/I/INT/X/RP/PK`; `singleton_key:INTEGER/N/S/I/INT/X/RP/AK,CHK,DEF(1)`; `current_schema_version:INTEGER/N/S/C/INT/E/RP/CHK`; `status:TEXT/N/S/C/INT/R/RP/CHK`; `active_attempt_id:INTEGER/?/S/C/INT/X/RP/FK→migration_attempt`; `recovery_set_ref:TEXT/N/S/C/PRV/X/RP`; `validation_status:TEXT/N/S/C/INT/R/RP/CHK`; `updated_at:TEXT/N/S/C/INT/R/RP` |

### 63.2 Owned-entity tables

| Table / owner / role | Lifecycle, retention, recovery | Complete columns |
|---|---|---|
| installation_context / LogicalInstallationRepository / retained lineage | Supersedable, restricted update; RP | `id:INTEGER/N/G/I/INT/X/RP/PK`; `installation_id:INTEGER/N/S/I/INT/X/RP/FK→logical_installation`; `predecessor_context_id:INTEGER/?/S/I/INT/X/RP/FK→installation_context`; `installation_scope:TEXT/N/S/I/PSN/R/RP/NK`; `secret_handle:TEXT/N/S/I/PRV/X/RP/NK`; `secret_generation:INTEGER/N/S/I/INT/X/RP/NK,CHK`; `format_version:INTEGER/N/S/I/PUB/E/RP/NK,CHK`; `status:TEXT/N/S/C/INT/R/RP/CHK`; `valid_from:TEXT/N/S/I/INT/R/RP`; `valid_until:TEXT/?/S/C/INT/R/RP`; `activation_audit_id:INTEGER/N/S/I/INT/X/RP/FK→audit_record` |
| clone_decision / LogicalInstallationRepository / immutable decision | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `context_id:INTEGER/N/S/I/INT/X/RH/FK→installation_context`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `declaration_id:INTEGER/?/S/I/INT/X/RH/FK→authoritative_declaration`; `provenance_reference_id:INTEGER/N/S/I/INT/X/RH/FK→protected_provenance_reference`; `classification:TEXT/N/S/I/INT/E/RH/CHK`; `ambiguity_state:TEXT/N/S/I/INT/R/RH/CHK`; `activation_outcome:TEXT/N/S/I/INT/R/RH/CHK`; `decided_at:TEXT/N/S/I/INT/R/RH`; `decision_digest:BLOB/N/D/I/INT/X/RH/DIGEST`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record` |
| activation_outcome / LogicalInstallationRepository / immutable outcome | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `context_id:INTEGER/N/S/I/INT/X/RH/FK→installation_context`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `clone_decision_id:INTEGER/N/S/I/INT/X/RH/FK→clone_decision`; `compatibility_decision_id:INTEGER/N/S/I/INT/X/RH/FK→compatibility_decision`; `secret_validation:TEXT/N/S/I/PRV/X/RH/CHK`; `provenance_validation:TEXT/N/S/I/PRV/X/RH/CHK`; `requested_state:TEXT/N/S/I/INT/R/RH/CHK`; `result_state:TEXT/N/S/I/INT/E/RH/CHK`; `safe_failure_code:TEXT/?/S/I/INT/R/RH`; `recorded_at:TEXT/N/S/I/INT/R/RH`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record` |
| authoritative_declaration / LogicalInstallationRepository / immutable version | Supersedable by insert, never update; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `declaration_key:TEXT/N/S/I/PRV/X/RH/NK`; `declaration_version:INTEGER/N/S/I/INT/R/RH/NK,CHK`; `protected_content_ref:TEXT/N/S/I/PRV/X/RH`; `authority_status:TEXT/N/S/I/INT/R/RH/CHK`; `integrity_status:TEXT/N/S/I/PRV/X/RH/CHK`; `valid_from:TEXT/N/S/I/INT/R/RH`; `valid_until:TEXT/?/S/I/INT/R/RH` |
| protected_provenance_reference / LogicalInstallationRepository / immutable external ref | Supersedable by insert; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `installation_id:INTEGER/N/S/I/INT/X/RH/FK→logical_installation`; `context_id:INTEGER/N/S/I/INT/X/RH/FK→installation_context`; `provider_ref:TEXT/N/S/I/PRV/X/RH/NK`; `provider_version:TEXT/N/S/I/PRV/X/RH/NK`; `integrity_status:TEXT/N/S/I/PRV/X/RH/CHK`; `availability_status:TEXT/N/S/I/INT/R/RH/CHK`; `created_at:TEXT/N/S/I/INT/R/RH` |
| identity_registration / CollisionRegistryRepository / retained identity | Append-retain; retirement fields controlled; RP | `id:INTEGER/N/G/I/INT/X/RP/PK`; `registry_id:INTEGER/N/S/I/INT/X/RP/FK→collision_registry`; `context_id:INTEGER/N/S/I/INT/X/RP/FK→installation_context`; `reference_kind:TEXT/N/S/I/PUB/E/RP/NK,CHK`; `format_version:INTEGER/N/S/I/PUB/E/RP/NK,CHK`; `canonical_tuple_handle:TEXT/N/S/I/PRV/X/RP/NK`; `opaque_reference:TEXT/N/S/I/PSN/E/RP/AK`; `secret_generation:INTEGER/N/S/I/INT/X/RP/NK,CHK`; `status:TEXT/N/S/C/INT/R/RP/CHK`; `registered_at:TEXT/N/S/I/INT/R/RP`; `retired_at:TEXT/?/S/C/INT/R/RP`; `registration_audit_id:INTEGER/N/S/I/INT/X/RP/FK→audit_record`; `identity_digest:BLOB/N/D/I/INT/X/RP/DIGEST` |
| entity_current_state / EntityRepository / current projection | Mutable only via lifecycle UoW; RC | `id:INTEGER/N/G/I/INT/X/RC/PK`; `entity_id:INTEGER/N/S/I/INT/X/RC/FK→entity,AK`; `lifecycle_state:TEXT/N/S/C/INT/E/RC/CHK`; `effective_at:TEXT/N/S/C/INT/R/RC`; `source_event_id:INTEGER/N/S/C/INT/X/RC/FK→entity_lifecycle_event`; `scan_run_id:INTEGER/N/S/C/INT/X/RC/FK→scan_run`; `audit_id:INTEGER/N/S/C/INT/X/RC/FK→audit_record` |
| entity_lifecycle_event / EntityRepository / immutable history | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `entity_id:INTEGER/N/S/I/INT/X/RH/FK→entity`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `prior_state:TEXT/?/S/I/INT/R/RH/CHK`; `result_state:TEXT/N/S/I/INT/E/RH/CHK`; `observation_id:INTEGER/N/S/I/INT/X/RH/FK→observation`; `scan_run_id:INTEGER/N/S/I/INT/X/RH/FK→scan_run`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record`; `event_at:TEXT/N/S/I/INT/R/RH`; `reason_code:TEXT/N/S/I/INT/R/RH` |
| relationship_current_state / RelationshipRepository / current projection | Mutable only via relationship UoW; RC | `id:INTEGER/N/G/I/INT/X/RC/PK`; `relationship_id:INTEGER/N/S/I/INT/X/RC/FK→relationship,AK`; `status:TEXT/N/S/C/INT/E/RC/CHK`; `predicate:TEXT/?/S/C/PUB/E/RC`; `source_ref:TEXT/?/S/C/PSN/E/RC`; `target_ref:TEXT/?/S/C/PSN/E/RC`; `effective_at:TEXT/N/S/C/INT/R/RC`; `source_event_id:INTEGER/N/S/C/INT/X/RC/FK→relationship_lifecycle_event`; `scan_run_id:INTEGER/N/S/C/INT/X/RC/FK→scan_run` |
| relationship_lifecycle_event / RelationshipRepository / immutable history | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `relationship_id:INTEGER/N/S/I/INT/X/RH/FK→relationship`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `event_kind:TEXT/N/S/I/INT/R/RH/CHK`; `prior_predicate:TEXT/?/S/I/PUB/E/RH`; `prior_source_ref:TEXT/?/S/I/PSN/E/RH`; `prior_target_ref:TEXT/?/S/I/PSN/E/RH`; `result_predicate:TEXT/?/S/I/PUB/E/RH`; `result_source_ref:TEXT/?/S/I/PSN/E/RH`; `result_target_ref:TEXT/?/S/I/PSN/E/RH`; `continuity:TEXT/N/S/I/INT/R/RH/CHK`; `observation_id:INTEGER/N/S/I/INT/X/RH/FK→observation`; `scan_run_id:INTEGER/N/S/I/INT/X/RH/FK→scan_run`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record`; `event_at:TEXT/N/S/I/INT/R/RH` |
| scan_capability_outcome / ScanRunRepository / immutable terminal detail | Insert before terminalization, immutable afterward; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `scan_run_id:INTEGER/N/S/I/INT/X/RH/FK→scan_run`; `capability_id:TEXT/N/S/I/PUB/E/RH/NK`; `status:TEXT/N/S/I/INT/E/RH/CHK`; `retryable:INTEGER/?/S/I/INT/R/RH/CHK`; `safe_error_code:TEXT/?/S/I/INT/R/RH`; `observation_contribution:INTEGER/N/S/I/INT/R/RH/CHK,DEF(0)`; `completeness_contribution:TEXT/N/S/I/INT/R/RH/CHK`; `recorded_at:TEXT/N/S/I/INT/R/RH` |
| migration_attempt / MigrationStateRepository / terminal history | Mutable only until terminal; then immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `migration_state_id:INTEGER/N/S/I/INT/X/RH/FK→migration_state`; `migration_id:TEXT/N/S/I/INT/E/RH/AK`; `idempotency_key:TEXT/N/S/I/INT/X/RH/AK`; `from_version:INTEGER/N/S/I/INT/E/RH/CHK`; `to_version:INTEGER/N/S/I/INT/E/RH/CHK`; `started_at:TEXT/N/S/I/INT/R/RH`; `finished_at:TEXT/?/S/T/INT/R/RH`; `status:TEXT/N/S/T/INT/R/RH/CHK`; `recovery_set_validation:TEXT/N/S/I/PRV/X/RH/CHK`; `safe_error_code:TEXT/?/S/T/INT/R/RH`; `audit_id:INTEGER/N/S/T/INT/X/RH/FK→audit_record`; `migration_checksum:BLOB/N/S/I/INT/X/RH/DIGEST` |

### 63.3 Association tables

| Table / owner / role | Lifecycle, retention, recovery | Complete columns |
|---|---|---|
| observation_subject_link / ObservationRepository / reference | Immutable with observation; follows observation retention | `id:INTEGER/N/G/I/INT/X/RH/PK`; `observation_id:INTEGER/N/S/I/INT/X/RH/FK→observation`; `subject_kind:TEXT/N/S/I/INT/R/RH/CHK`; `subject_id:INTEGER/N/S/I/INT/X/RH`; `role:TEXT/N/S/I/INT/R/RH/AK` |
| audit_evidence_link / AuditRepository / N:N evidence | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record`; `observation_id:INTEGER/N/S/I/INT/X/RH/FK→observation`; `role:TEXT/N/S/I/INT/R/RH/AK`; `ordinal:INTEGER/N/S/I/INT/R/RH/CHK` |
| audit_subject_link / AuditRepository / N:N subject | Append-only immutable; RH | `id:INTEGER/N/G/I/INT/X/RH/PK`; `audit_id:INTEGER/N/S/I/INT/X/RH/FK→audit_record`; `subject_kind:TEXT/N/S/I/INT/R/RH/CHK`; `subject_id:INTEGER/N/S/I/INT/X/RH`; `role:TEXT/N/S/I/INT/R/RH/AK` |

Catalogue count: **25 tables, 243 columns**. Conditional nulls are governed by
closed-status checks; no optional field may become an inference channel.

## 64. Identifier and digest representation

| Identifier | Physical representation | Scope/constraint |
|---|---|---|
| Synthetic table PK | Positive SQLite INTEGER, engine assigned | Internal only; one per table; immutable. |
| LogicalInstallation identity | logical_installation INTEGER PK | Sole canonical installation identity; never exported. |
| Installation scope | Canonical TEXT | Validated accepted scope; never a hardware fingerprint. |
| `source_ref` | Exact accepted `refh1_entity_` plus 64 lowercase hex TEXT | 77 ASCII octets; frozen CA-001/AI-002 semantics; scoped uniqueness. |
| `target_ref` | Canonical TEXT under frozen target grammar | Not assumed Entity; validated before write. |
| Identity/collision registration | INTEGER PK plus scoped canonical-handle/opaque-ref alternate keys | Handle is protected metadata; full 32-octet identity digest BLOB. |
| Scan/event/decision/audit idempotency | Canonical UUID-form lowercase TEXT supplied by transaction boundary | Scoped alternate unique key; conflicting retry fails. |
| Public relationship ID | Exact accepted opaque relationship-ID TEXT | Scoped to installation and canonical tuple semantics. |
| Dataset/bundle reference | Canonical provider-qualified TEXT plus version TEXT and 32-octet digest BLOB where retained in audit/activation payload | External read-only artifact reference only. |
| Schema/generation versions | Non-negative INTEGER | Never conflated with public contract/version text. |
| Bundle/contract/implementation versions | Canonical non-empty TEXT | Independent VersionState dimensions. |
| Immutable/migration/bundle digests | Exactly 32-octet BLOB | SHA-256; compared byte-for-byte; not a secret. |

## 65. Physical enforcement of LC-001–LC-030

| Constraint | Physical owner | Primary mechanism | Failure and recovery | Later test obligation |
|---|---|---|---|---|
| LC-001 | collision_registry | UNIQUE installation_id | Duplicate registry rejected; use existing valid root | Duplicate insert/concurrent retry |
| LC-002 | logical_installation/current context | Unique active-context transaction plus scoped unique index | Activation rollback; prior context remains | Two eligible contexts/race |
| LC-003 | installation_context activation | SECRET_STORE_BOUNDARY + transaction validation | Fail closed; restore matching secret | Missing/wrong/malformed secret |
| LC-004 | installation_context lineage | TRANSACTION_SERVICE recursive lineage validation | Reject cycle/cross-owner link | Self/cycle/cross-installation |
| LC-005 | identity_registration | UNIQUE(registry, context, kind, format, canonical handle, generation) | Collision transaction rollback | Same/different payload collision |
| LC-006 | identity_registration | UNIQUE(registry, context, kind, format, opaque reference) | Fail closed, publish nothing | Opaque collision |
| LC-007 | identity_registration | TRIGGER requirement forbidding delete and identity-field update | Reject purge/mutation; restore on corruption | Update/delete attempts |
| LC-008 | entity | FOREIGN KEYs plus UNIQUE identity_registration_id | Reject orphan/duplicate entity | Missing/cross-scope registration |
| LC-009 | entity_current_state | UNIQUE entity_id | Reject second current projection | Duplicate/race |
| LC-010 | entity_current_state/events | CHECK closed five-state set excluding HISTORICAL current | Reject invalid state | Every valid/invalid enum |
| LC-011 | entity transition UoW | TRANSACTION_SERVICE | Rollback and retain prior projection | Closed transition matrix |
| LC-012 | relationship | UNIQUE scoped public ID and UNIQUE scoped canonical tuple | Reject duplicate/conflict | Duplicate ID/tuple |
| LC-013 | relationship | FOREIGN KEY source_entity_id plus transaction equality to source_ref | Reject mismatched source | Missing/mismatched source ref |
| LC-014 | relationship | APPLICATION_VALIDATION frozen target grammar | Reject before insert | Valid/invalid/non-Entity target |
| LC-015 | relationship_current_state | UNIQUE relationship_id | Reject second projection | Duplicate/race |
| LC-016 | relationship UoW | TRANSACTION_SERVICE | Rollback ambiguous continuity/recreation | Complete transition matrix |
| LC-017 | scan_run | UNIQUE(installation_id,idempotency_key) | Return same semantic run or reject conflict | Matching/conflicting retry |
| LC-018 | scan_run/capability outcomes | TRIGGER requirement preventing terminal rewrite/outcome mutation | Reject rewrite | Every terminal transition/rewrite |
| LC-019 | complete-scan UoW | TRANSACTION_SERVICE reads terminal completeness | Preserve current state | Failed/partial absence |
| LC-020 | scan_capability_outcome | UNIQUE(scan_run_id,capability_id) | Idempotent or conflict | Duplicate capability result |
| LC-021 | observation | CHECK closed taxonomy/retention/privacy combinations | Reject observation | All allowed/disallowed pairs |
| LC-022 | normalization boundary | APPLICATION_VALIDATION/privacy allowlist | Reject payload, safe failure only | Secret/raw/PII leakage corpus |
| LC-023 | immutable tables | TRIGGER requirement forbidding UPDATE/DELETE | Reject mutation | Each immutable table mutation |
| LC-024 | association tables | FOREIGN KEY fixed refs + transaction validation tagged subject | Reject dangling/tag mismatch | FK and every subject kind |
| LC-025 | audit_record/UoW | UNIQUE idempotency + TRANSACTION_SERVICE mandatory audit | Entire transition rollback | Missing/duplicate/conflicting audit |
| LC-026 | compatibility_decision | CHECK closed result/outcome combinations | Reject or fail capability closed | Full compatibility matrix |
| LC-027 | version_state/startup | MIGRATION_VALIDATION plus non-negative checks | Refuse startup/write | Forward/negative/mismatch versions |
| LC-028 | migration UoW | TRANSACTION_SERVICE serialized IMMEDIATE transaction | Rollback or blocking incomplete state | Concurrent/interrupted/checksum failure |
| LC-029 | retention UoW | TRANSACTION_SERVICE reference/policy proof | Reject purge | Referenced A–F and allowed G/J/L |
| LC-030 | all scoped writes | TRANSACTION_SERVICE + scoped UNIQUE/FK checks | Fail closed, publish nothing | Cross-installation references/aliases |

Primary enforcement counts: UNIQUE/unique-index 9; trigger 3; fixed foreign-key
2; CHECK 3; transaction service 9; application validation 2; secret-store
boundary 1; migration validation 1. Total: **30**.

## 66. Foreign-key policy and registry

There are **57 fixed physical foreign keys** in section 63. Every fixed FK uses
`ON UPDATE RESTRICT`. Default deletion is `ON DELETE RESTRICT`; only the three
association tables may delete their own links when their owner record is
retention-eligible, and no FK cascades into an aggregate, history, identity or
audit table.

| Child group → parent | Cardinality/nullability | Delete/history policy |
|---|---|---|
| installation/context/registry/entity/relationship groups → logical_installation | N:1 mandatory except current_context pointer nullable | RESTRICT; installation retirement is soft and history retained. |
| logical_installation.current_context_id → installation_context | 0..1:1 | RESTRICT; pointer changed only by activation UoW. |
| context predecessor → installation_context | 0..1:1 self reference | RESTRICT; lineage cannot be deleted. |
| identity_registration → collision_registry/context/audit | N:1 mandatory | RESTRICT; registrations retained. |
| entity → context/registration | N:1 mandatory | RESTRICT; removal is lifecycle state. |
| current state/event → entity, run, observation, audit/event | N:1 mandatory except creation prior state | RESTRICT; current replacement never deletes history. |
| relationship → entity and installation | N:1 mandatory | RESTRICT; target_ref is validated TEXT, not a false Entity FK. |
| relationship current/event → relationship, run, observation, audit/event | N:1 mandatory as catalogued | RESTRICT; relationship removal is soft/current-state transition. |
| scan/capability/observation → installation/context/run | N:1 mandatory | RESTRICT while retained evidence depends on run. |
| decisions/outcomes → installation/context/run/decision/audit | N:1 with explicitly nullable startup/run refs | RESTRICT; decisions immutable. |
| version/migration current pointers → attempts | 0..1:1 | RESTRICT; pointer clears/advances only in migration UoW. |
| association links → observation/audit | N:1 mandatory | Links may be removed only with retention-eligible owner; no subject cascade. |

Tagged `subject_id` is not a fixed FK because SQLite cannot safely reference
several parent tables from one column. LC-024 transaction validation is
mandatory. Audit/history records cannot be deleted through current projection
operations.

## 67. Named physical index disposition

All are mandatory for schema version 1 unless marked “defer”; none is partial
unless its predicate is stated.

| Index | Table / ordered columns | Unique/partial | Supports / cost |
|---|---|---|---|
| ix_context_installation_status | installation_context(installation_id,status,valid_from) | nonunique; current-status predicate eligible | Context lookup/lineage; moderate context-write cost. |
| ix_registration_registry_kind_status | identity_registration(registry_id,reference_kind,status,registered_at) | nonunique | Collision/history lookup; retained index growth. |
| ix_entity_installation_context_status | entity(installation_id,context_id,identity_status,id) | nonunique | Installation entity/current identity scans. |
| ix_entity_state_value_time | entity_current_state(lifecycle_state,effective_at,entity_id) | nonunique | Current-state lookup. |
| ix_entity_event_chronology | entity_lifecycle_event(entity_id,event_at,id) | nonunique | Deterministic lifecycle replay. |
| ix_relationship_traversal | relationship(installation_id,predicate,source_ref,target_ref,id) | nonunique; candidate-key overlap reviewed | Relationship traversal; write cost accepted. |
| ix_relationship_state_time | relationship_current_state(status,effective_at,relationship_id) | nonunique | Current relationship status. |
| ix_relationship_event_chronology | relationship_lifecycle_event(relationship_id,event_at,id) | nonunique | Relationship replay. |
| ix_scan_installation_status_time | scan_run(installation_id,status,started_at,id) | nonunique | Scan membership/recovery. |
| ix_capability_run_status | scan_capability_outcome(scan_run_id,status,capability_id) | nonunique | Completeness calculation; may overlap AK. |
| ix_observation_run_class_time | observation(scan_run_id,taxonomy_class,observed_at,id) | nonunique | Observation chronology. |
| ix_observation_subject | observation_subject_link(subject_kind,subject_id,observation_id) | nonunique | Subject evidence lookup. |
| ix_compatibility_context_result_time | compatibility_decision(installation_id,context_id,result,decided_at,id) | nonunique | Compatibility/activation lookup. |
| ix_audit_installation_kind_time | audit_record(installation_id,event_kind,recorded_at,id) | nonunique | Audit chronology. |
| ix_audit_evidence_observation | audit_evidence_link(observation_id,audit_id) | nonunique | Reverse evidence lookup. |
| ix_audit_subject | audit_subject_link(subject_kind,subject_id,audit_id) | nonunique | Subject audit lookup. |
| ix_migration_order_status | migration_attempt(migration_state_id,to_version,status,started_at,id) | nonunique | Migration recovery/order. |
| ix_external_versions | version_state(hask_bundle_ref,hudd_ref,contract_version,validation_status) | nonunique; singleton, defer physically if query plan proves redundant | Dataset/bundle compatibility lookup; negligible rows but retained as disposition. |

Candidate-key uniqueness creates additional key indexes. Physical migration
review may omit only a provably redundant secondary index and must record the
equivalent covering key; it may not silently lose an invariant.

## 68. Current, immutable and retention enforcement

| Physical class | Tables | Enforcement |
|---|---|---|
| Mutable current projection | logical_installation, collision_registry status, entity status, relationship status, entity_current_state, relationship_current_state, version_state, migration_state | Only named UoWs; optimistic prior-state check plus IMMEDIATE transaction; projection/event/audit commit together. |
| Mutable until terminal | scan_run, migration_attempt | Trigger rejects changes after terminal state; safe terminal fields become immutable. |
| Supersedable by new row, not update | authoritative_declaration, protected_provenance_reference | Trigger forbids UPDATE/DELETE; new version row plus audit supersedes. |
| Append-retained with restricted status transition | installation_context, identity_registration | Identity/lineage fields immutable; trigger permits only closed status/end-time transition; delete forbidden. |
| Fully append-only immutable | clone_decision, activation_outcome, observation, compatibility_decision, audit_record, entity_lifecycle_event, relationship_lifecycle_event, terminal scan_capability_outcome, observation_subject_link, audit_evidence_link, audit_subject_link | BEFORE UPDATE/DELETE trigger requirement; repository discipline is defense-in-depth. |
| Reconstructable/deletable | No canonical J/L tables; G diagnostics are not in schema 1 | Generated views/reports rebuilt outside DB. |

Count: **11 fully immutable table families plus 2 supersedable immutable tables**;
identity/context and terminal tables have narrower trigger protection. Trigger
enforcement prevents accidental/admin-path mutation across all writers;
repository discipline supplies meaningful errors and valid transitions. Triggers
must remain small and deterministic; multi-row semantic rules stay in the
transaction service. Periodic integrity validation checks projection/event/audit
agreement. LifecycleHistory remains a query/view over event tables, never a
table.

## 69. SQLite runtime configuration

| Setting | Required value/range | Owner/startup validation/failure |
|---|---|---|
| foreign_keys | ON for every connection | Connection factory verifies; failure blocks activation. |
| journal_mode | WAL | Database initialization verifies persisted mode; failure blocks writer startup. |
| synchronous | FULL | Connection factory verifies; weaker value is rejected for identity writes. |
| busy_timeout | 5000 ms initial | Connection owner sets/verifies; exhaustion rolls back and reports safe busy failure. |
| write transaction | IMMEDIATE, one serialized logical writer | Transaction service; inability to acquire within bounded policy writes nothing. |
| recursive_triggers | ON | Connection factory verifies for trigger enforcement; failure blocks writes. |
| trusted_schema | OFF | Connection factory verifies; failure blocks operational activation. |
| temp_store | MEMORY | Connection factory verifies where supported; prevents temp operational values spilling by default. |
| wal_autocheckpoint | 1000 pages initial | Database owner monitors; explicit passive checkpoint at idle/backup boundary. |
| quick_check | Successful at startup before activation | Recovery manager; failure enters read-only recovery/fail-closed mode. |
| integrity_check | Successful before/after migration, after restore, and on explicit deep validation | Migration/recovery owner; failure blocks activation. |
| application_id | `0x4841534B` (“HASK”) | Bootstrap/startup exact match; wrong nonzero ID rejects database. |
| user_version | Supplementary mirror of authoritative schema_version | Startup requires equality; mismatch fails closed. |
| page_size | SQLite/default platform value; no mandate | Changing requires later measured evidence and migration review. |

Backups use a SQLite-consistent online backup/checkpoint-aware mechanism; copying
only the live main file is invalid while WAL may contain committed pages.

## 70. Physical schema-version and migration evidence

- `version_state.schema_version` and `migration_state.current_schema_version`
  are authoritative and must agree.
- `user_version` is a supplementary fast mirror, checked but never sufficient.
- `migration_attempt` owns migration identity, from/to versions, 32-octet
  migration checksum, timestamps, status, recovery-set validation, safe failure
  and audit reference.
- Application compatibility is evaluated against VersionState and the supported
  schema range before writes.
- An in-progress/failed attempt remains explicit; restart cannot mark it
  successful from target objects alone.
- Migration checksum mismatch, forward version, version triple mismatch or
  failed integrity check enters fail-closed recovery mode.
- Public contract, architecture, implementation, HASK knowledge and HUDD schema
  versions remain separate. Contract 1.0.0 remains active.

## 71. Eight-phase physical dependency map

| Phase | Tables / prerequisite | Constraints and indexes | Bootstrap/transaction/recovery validation |
|---|---|---|---|
| 1 Schema governance | migration_state, migration_attempt; empty recognized HASK DB | PK/singleton/checksum/status; ix_migration_order_status | Exclusive bootstrap; application_id; initial state/version; rollback whole phase. |
| 2 Version foundation | version_state; phase 1 | Singleton/version checks; ix_external_versions disposition | Authoritative version row + user_version mirror; mismatch blocks. |
| 3 Installation foundation | logical_installation, installation_context, authoritative_declaration, protected_provenance_reference; phase 2 | Context/recovery/declaration/provenance keys; ix_context_installation_status | Bootstrap recovery set; create atomically where cyclic FKs deferred until all tables exist; validate secret externally. |
| 4 Identity foundation | collision_registry, identity_registration; phase 3 | LC-001/005/006/007; ix_registration_registry_kind_status | Create registry then register only through IMMEDIATE collision UoW; restore on failure. |
| 5 Operational subjects | entity, entity_current_state, relationship, relationship_current_state; phase 4 | Entity/relationship/current keys and indexes | Create tables before data; projections require later event/audit refs and are populated only after phases 6–8. |
| 6 Collection facts | scan_run, scan_capability_outcome, observation, observation_subject_link; phase 5 | Run/observation/link keys and chronology indexes | No initial seed rows; validate taxonomy/privacy checks. |
| 7 History/decisions | entity_lifecycle_event, relationship_lifecycle_event, clone_decision, compatibility_decision, activation_outcome; phase 6 | Immutable/idempotency/chronology constraints | Install append-only triggers; no activation eligibility yet. |
| 8 Audit closure | audit_record, audit_evidence_link, audit_subject_link; phase 7 | Audit/link keys, append-only triggers, audit indexes, all FK checks | Close deferred cycles, run foreign_key_check/integrity checks, record bootstrap audit, then mark activation eligible. |

Each phase is one exclusive transaction where SQLite supports the operations.
Failure before commit rolls back; post-commit validation failure requires a
forward-fix migration or restoration of the pre-phase recovery set—never silent
down-migration.

## 72. Ten physical unit-of-work mappings

| UoW | Tables / order / pre-read | Transaction, commit, rollback, evidence/idempotency |
|---|---|---|
| Installation bootstrap | Read version/migration/secret; write logical_installation → provenance/declaration → context → registry → compatibility/activation → audit/link → current pointer | EXCLUSIVE for first bootstrap, otherwise IMMEDIATE; commit only after secret/provenance/version/FK checks; request key; rollback all. |
| Scan start | Read installation/context/active state; insert scan_run(running) | IMMEDIATE short transaction; unique run key; no observation/state write; rollback on inactive context/conflict. |
| Scan completion | Read running run/capability completeness/current projections; insert outcomes/observations/links → lifecycle/relationship events → audit/links → update projections → terminalize run | IMMEDIATE; complete authority required; commit all or rollback; run/observation/transition keys. |
| Entity discovery/update | Read registration/current entity; collision UoW if new; insert entity/event/audit then current projection or update projection | IMMEDIATE; uniqueness/source checks; no entity without registration/audit. |
| Collision registration | Read registry/context and both unique candidates; insert identity_registration + audit/link | IMMEDIATE; unique violation fails closed; canonical registration idempotency. |
| Relationship transition | Read source Entity/ref, frozen target validation, current tuple/history; insert relationship if new/event/audit then replace current projection | IMMEDIATE; tuple/transition keys; rollback ambiguity/dangling endpoint. |
| Lifecycle transition | Read current state, complete run/evidence; insert event/audit/link then replace entity_current_state | IMMEDIATE; prior-state compare; rollback invalid transition. |
| Removal | Read complete run or positive removal evidence/current relationship dependencies; append events/audit then mark current states; never delete identity/history | IMMEDIATE; absence on partial/failed run rolls back/no-op; transition idempotency. |
| Compatibility decision | Read VersionState/context/bundle ref; insert compatibility_decision/audit/link then activation outcome or fail-closed capability state | IMMEDIATE; decision key; incompatible/unknown never activates capability. |
| Migration execution | EXCLUSIVE read integrity/version/checksum/recovery marker; open attempt → transform phase → validate FK/integrity → audit → version/current attempt terminal updates | EXCLUSIVE; migration idempotency/checksum; rollback transaction or retain explicit failed blocking attempt and restore/forward-fix. |

All threads submit to the single writer. No independent process may execute
these write sequences.

## 73. Bundle/reference representation and seed boundary

No producer, brand, underbrand, support-code or masterlist catalogue table is
present. Research seeds remain in HASK/HUDD offline build contexts.

The operational representation is a versioned external-bundle reference carried
by VersionState plus immutable CompatibilityDecision, ActivationOutcome and
AuditRecord context. The normalized reference comprises: provider-qualified
bundle reference, bundle version, 32-octet digest, contract version,
compatibility result, activation timestamp/outcome, optional previous-bundle
reference and optional rollback reference. These values are stored in the
appropriate existing relations as canonical TEXT/BLOB/audit attributes; they do
not justify a 26th table. Bundle bytes remain read-only and external.

## 74. Backup, restore and corruption recovery

- **Safe boundary:** operational DB consistent image + matching protected secret
  generation + protected provenance + identity-relevant configuration, labeled
  as one recovery set.
- **WAL:** use SQLite-consistent backup/checkpoint semantics; never copy only a
  live main file.
- **Restore validation:** application_id, quick_check/integrity_check,
  foreign_key_check, authoritative schema/user_version agreement, migration
  checksums/status, singleton roots, secret/provenance match, collision-registry
  integrity, bundle digest/compatibility and projection/event/audit consistency.
- **Failure mode:** open read-only recovery diagnostics where safe; identity
  activation and all writes remain disabled. No secret/scope/reference is
  regenerated.
- **Non-rebuildable:** logical installation/context, collision/registration,
  required A–F observations, lifecycle events, decisions/audit, version and
  migration evidence.
- **Rebuildable:** generated reports/views, J/L projections, HASK bundle and HUDD
  artifacts after independent checksum/version validation; no canonical G table
  exists initially.
- Corruption of append-only history or registry requires validated restore or a
  separately governed forward repair; current projections alone cannot repair
  authority.

## 75. Repository-owner physical responsibilities

| Owner | Writes / references | Transactions, errors, queries and recovery |
|---|---|---|
| LogicalInstallationRepository | Writes installation/context/clone/activation/declaration/provenance tables; reads secret/version/compatibility/audit refs | Participates bootstrap/clone/activation; translates scope/context/idempotency/FK failures; queries current context/lineage; restores with recovery set. |
| CollisionRegistryRepository | Writes registry/registration; references context/audit | Owns IMMEDIATE collision transaction and unique-collision translation; lookup by canonical handle/opaque ref; registry restore/fail-close. |
| EntityRepository | Writes entity/current/event; references registration/run/observation/audit | Entity/lifecycle/removal UoWs; translates state/unique/FK failures; current/history queries; rebuild projection only from retained authority. |
| RelationshipRepository | Writes relationship/current/event; reads Entity/source registration/observation/audit | Relationship/removal UoWs; tuple/target/continuity errors; traversal/history queries; reconstruct current from events. |
| ScanRunRepository | Writes run/capability outcomes; references installation/context | Scan start/completion; terminal/idempotency errors; run chronology/completeness queries; interrupted recovery as non-complete. |
| ObservationRepository | Writes observation/subject links; reads run/subjects | Complete/partial scan participation; privacy/taxonomy/digest/link failures; run/subject chronology; restore required classes. |
| CompatibilityDecisionRepository | Writes compatibility decisions; reads version/context/bundle refs and audit | Compatibility/activation UoW; closed-result/idempotency errors; latest-by-context queries; reevaluation creates new decision. |
| AuditRepository | Writes audit/evidence/subject links only; reads all referenced roots | Participates every governed UoW; immutable/idempotency/link failures; chronology/reverse-evidence queries; backup-only recovery. |
| VersionStateRepository | Writes singleton only through migration/activation compatibility; reads external versions | Startup/migration/compatibility; singleton/version mismatch errors; current-vector query; restore/forward migration. |
| MigrationStateRepository | Writes migration state/attempt; references version/audit/recovery set | EXCLUSIVE migration; checksum/order/status errors; attempt chronology; rollback/restore/forward-fix coordination. |

These are access responsibilities, not method signatures or code interfaces.

## 76. Physical SQLite schema diagram

```text
EXTERNAL (never tables here)
 [Secret Store]   [HASK Bundle RO]   [HUDD RO]   [Config]
       │handle          │ref/digest      │ref        │ref
       └───────────────┬┴────────────────┴───────────┘
                       ▼
┌──────────────── HASK OPERATIONAL SQLITE ───────────────────────────┐
│ version_state [CURRENT]        migration_state [CURRENT]           │
│                                      └─< migration_attempt [HIST]  │
│                                                                    │
│ logical_installation [ROOT/CURRENT]                                │
│  ├─< installation_context [RETAINED LINEAGE]                       │
│  │    └─< protected_provenance_reference [IMMUTABLE VERSIONS]      │
│  ├─< authoritative_declaration [IMMUTABLE VERSIONS]                │
│  ├─1 collision_registry [RETAINED]                                 │
│  │    └─< identity_registration [COLLISION HISTORY]                │
│  ├─< clone_decision [IMMUTABLE]                                    │
│  ├─< compatibility_decision [IMMUTABLE]                            │
│  └─< activation_outcome [IMMUTABLE]                                │
│                                                                    │
│ entity [ROOT] ─1 entity_current_state [CURRENT]                    │
│    └─< entity_lifecycle_event [HISTORY/IMMUTABLE]                  │
│                                                                    │
│ relationship [ROOT; source→entity, target_ref frozen TEXT]         │
│    ├─1 relationship_current_state [CURRENT]                        │
│    └─< relationship_lifecycle_event [HISTORY/IMMUTABLE]            │
│                                                                    │
│ scan_run [ROOT/TERMINAL]                                           │
│    ├─< scan_capability_outcome [IMMUTABLE WHEN TERMINAL]           │
│    └─< observation [ROOT/IMMUTABLE]                                │
│          └─< observation_subject_link [ASSOCIATION]                │
│                                                                    │
│ audit_record [ROOT/APPEND-ONLY]                                    │
│    ├─< audit_evidence_link >─ observation                          │
│    └─< audit_subject_link  >─ tagged aggregate/event subject       │
│                                                                    │
│ Dashed conceptual cross-links: events/decisions → observation,    │
│ scan_run and audit_record; all are fixed RESTRICT FKs where typed. │
└────────────────────────────────────────────────────────────────────┘

LifecycleHistory = ordered event query/view only; no table.
Reports/API = external regenerated privacy-filtered projections.
```

## 77. DB-001F validation and next-batch gate

| Check | Result |
|---|---|
| Logical relations mapped exactly once | PASS — 25 tables |
| Physical columns fully catalogued | PASS — 243 |
| Primary candidate keys represented | PASS — 25 INTEGER PKs |
| Alternate candidate keys represented | PASS — 28 scoped UNIQUE candidates |
| Fixed foreign keys | PASS — 57, restrictive deletion |
| LC constraints mapped | PASS — 30 with owner/mechanism/failure/test duty |
| Constraint primary mechanisms | PASS — 9 unique, 3 trigger, 2 FK, 3 CHECK, 9 transaction, 2 application, 1 secret, 1 migration |
| Conceptual index families dispositioned | PASS — 18 named indexes |
| Logical relationships physically represented | PASS — 26, including tagged-reference validation |
| Unit-of-work boundaries mapped | PASS — 10 |
| Retention/current/history enforcement | PASS |
| Fully immutable + supersedable immutable families | 11 + 2 |
| SQLite PRAGMA decisions | PASS — 14 settings/validation decisions |
| Migration dependency phases | PASS — 8 |
| LifecycleHistory duplicated as table | NO |
| LogicalInstallation sole canonical identity | PASS |
| CollisionRegistry installation-wide authority | PASS |
| `source_ref` frozen opaque entity reference | PASS |
| `target_ref` frozen/non-Entity-assumed | PASS |
| HASK/HUDD/secret/research seed boundaries preserved | PASS |
| Executable SQL/schema/migration artifact created | NO |
| Repository interface/code/test/fixture/dependency/config created | NO |
| Governance changed | NO |
| Contract `1.0.0` active; proposed `2.0.0` inactive | PASS |
| Implementation authorized or begun | NO |

Unresolved issues for DB-001G, none requiring physical redesign:

1. select the concrete non-Windows protected secret provider before
   implementation;
2. define repository error taxonomy and method-neutral operation contracts;
3. define executable-migration authoring/verification procedure and checksum
   manifest format under a later implementation authority;
4. produce the final cross-layer consistency/recovery/readiness review; and
5. classify implementation batches and governance gates.

Recommended next batch: **DB-001G — Repository, migration and
implementation-readiness plan plus final consistency and recovery review**.

The DB-001F validation above remains preserved. DB-001G below performs review
and close-out without redesigning DB-001A–F.

## 78. DB-001G completion decisions

| ID | Decision | Reason | Consequences | Future revisit trigger |
|---|---|---|---|---|
| DB001-D-033 | The DB-001 foundation is implementation-ready subject to a new implementation authority and the prerequisites in section 86. | Conceptual, logical, physical, transaction, migration, recovery and ownership reviews are complete with no architectural blocker. | Future implementation must conform; it may not invent schema semantics. | Independent implementation review finds an objective contradiction or missing architecture decision. |
| DB001-D-034 | Repository governance consists of ten exclusive owners, canonical error categories and transaction-level orchestration that never transfers aggregate ownership. | Prevents overlapping writes and engine errors leaking as domain semantics. | Future repositories translate errors consistently and participate only in authorized UoWs. | A governed ownership change or engine adapter requires another owner. |
| DB001-D-035 | Migrations are forward-only, ordered, checksummed, replay-safe, recovery-set guarded and repairable only by a later governed forward migration or restore. | Identity/history cannot tolerate ad-hoc mutation or silent checksum drift. | No down-migration or manual schema repair is part of normal operation. | An engine/platform cannot provide required transactional/validation behavior. |
| DB001-D-036 | Recovery is fail-closed for secret, collision, schema, migration, corruption and provenance failures; automatic action may only restore internally consistent engine state, never invent identity. | Preserves CA-001 and AI-002 identity stability after faults. | Operators restore matching recovery sets or apply governed repair; reports/caches may rebuild. | Accepted recovery architecture introduces a stronger verified repair path. |
| DB001-D-037 | Operational readiness requires successful startup PRAGMA/integrity/version/secret/provenance/bundle checks and serialized-writer ownership before activation. | Physical schema correctness alone is insufficient for safe operation. | Any failed mandatory gate leaves persistence inactive or read-only recovery mode. | Deployment requirements cross the DB001-D-003/D-004 escalation gate. |
| DB001-D-038 | DB-001 is COMPLETE as a documentation-only database foundation. | Its sole deliverable contains all required sections, decisions, classifications and implementation plan and passes section 87. | DB-001 completion does not authorize code, schema artifacts, migrations, tests, contract changes or deployment; a governance transition is still required. | Only a formally governed defect/review may reopen it. |

## 79. Portable protected-secret provider model

The provider is an external security boundary, not a repository or SQLite
table. Its conceptual contract is platform-neutral:

- **ownership:** a single SecretProvider owned by the future HADocs identity
  runtime owns CA-001 secret bytes; the operational DB owns only SecretHandle,
  generation and validation metadata;
- **capabilities:** cryptographically secure creation of exactly 32 octets,
  retrieval by opaque handle, existence/access validation, generation metadata,
  explicit backup/export-to-protected-recovery-set operation, protected restore,
  governed rotation and explicit destruction only after architecture-authorized
  retirement;
- **lifecycle:** `ABSENT → CREATED → AVAILABLE`; temporary access failure yields
  `UNAVAILABLE`; restore returns only the matching generation; rotation creates a
  new generation and never overwrites the old recovery identity silently;
- **confidentiality/integrity:** OS/container facility must encrypt or otherwise
  protect at rest, restrict access to the HADocs service identity, detect
  malformed/wrong-generation material and never return values to logs/reports;
- **portability:** Windows may use the existing Credential Manager precedent;
  Linux/container must supply a platform adapter satisfying the same semantic
  contract. No particular library, file format or orchestrator is selected;
- **failure:** missing, unreadable, malformed, mismatched or unauthorized secret
  returns a safe category and blocks identity activation/writes. Automatic
  generation is forbidden outside first authorized initialization;
- **backup coordination:** provider produces/restores a protected secret item
  carrying recovery-set identity and generation so the DB/provenance match can
  be validated before activation;
- **implementation responsibility:** a future implementation authority selects
  and threat-models adapters, tests permission/backup/failure behavior and proves
  secret bytes never cross the boundary.

This resolves the architecture abstraction. Concrete non-Windows adapter
selection remains an **implementation prerequisite**, not a DB-001 blocker.

## 80. Canonical repository error taxonomy

| Category | Meaning / origin owner | Translation and retry expectation |
|---|---|---|
| NOT_FOUND | Requested aggregate/reference does not exist; repository owns translation | No blind retry; caller may choose valid create/recovery path. |
| ALREADY_EXISTS | Candidate/idempotency identity exists with equivalent semantics | Treat as idempotent success only after payload/result equality; otherwise conflict. |
| CONSTRAINT_VIOLATION | Named SQLite key/FK/check/trigger invariant rejected the operation | Repository maps to stable constraint ID; no retry without corrected authoritative input. |
| VALIDATION_FAILURE | Input, enum, privacy, target grammar or semantic precondition failed before/around persistence | Validating boundary owns detail; no retry unchanged. |
| CONCURRENCY_CONFLICT | Busy/lock, stale prior projection or competing serialized operation | Transaction owner may bounded-retry transient lock; stale semantic conflicts require reread/redecision. |
| STORAGE_FAILURE | I/O/full/read-only/unavailable SQLite failure not proven corruption | Database owner translates safe engine code; retry only when classified transient and no partial commit. |
| CORRUPTION_DETECTED | Integrity/FK/application-ID/digest validation indicates corrupt or unrelated state | No write retry; enter recovery mode and restore/repair through governance. |
| MIGRATION_FAILURE | Migration checksum/order/pre/post-validation/transaction failed | Migration owner records safe failed attempt; restore or governed forward-fix, never normal retry guessing. |
| SECRET_UNAVAILABLE | Secret absent, unreadable, malformed, wrong generation or access denied | SecretProvider owns classification; bounded retry only for explicit temporary unavailability; no regeneration. |
| BUNDLE_MISMATCH | Bundle reference/digest/contract/compatibility differs from expected active state | Bundle/compatibility boundary deactivates provider; validate/reselect known bundle, never mutate DB identity. |
| VERSION_INCOMPATIBLE | DB schema or another required version dimension is unsupported | Startup/migration boundary fails closed; use compatible implementation or governed migration. |
| IDEMPOTENCY_CONFLICT | Same scoped idempotency key carries different normalized intent/result | Transaction owner rejects permanently until caller resolves key/intent; never overwrite. |

Repositories translate engine-specific failures to these categories and retain
the stable LC/index/operation identifier without exposing SQL, secrets or raw
payload. Transaction services translate multi-owner semantic failures. The
secret, migration and bundle boundaries originate their own categories. Only
CONCURRENCY_CONFLICT and explicitly transient STORAGE_FAILURE/SECRET_UNAVAILABLE
permit bounded automated retry; retry exhaustion preserves prior committed
state.

## 81. Migration authoring and repair policy

- Migration IDs are zero-padded monotonically increasing integers (`0001`,
  `0002`, ...), unique and gap/reorder protected within a released chain.
- One future migration artifact has one canonical byte representation and
  SHA-256 checksum. The release/build process owns the expected checksum;
  migration_attempt records the verified checksum and outcome.
- Authoring declares source/target schema version, prerequisite migration,
  affected tables/invariants, backup requirement, forward transformation,
  pre/post validation and recovery notes.
- Validation order is: application_id → integrity/foreign keys → authoritative
  schema/migration state → artifact ID/checksum → supported from-version →
  recovery-set marker → exclusive transaction → transformation → all affected
  constraints → full post-validation → audit/attempt terminalization → version
  advancement/user_version mirror.
- First application changes state once. Replay of an already successful matching
  ID/checksum/version is a verified no-op; a checksum or state mismatch fails
  closed. Failed/incomplete attempts never masquerade as applied.
- Evolution is forward-only. Transaction rollback is used before commit;
  post-commit rollback means restoring the validated pre-migration recovery set
  with the compatible prior implementation.
- Repair is never manual row/schema editing. It is either validated restore or a
  separately reviewed, checksummed forward repair migration that preserves
  collision/history/audit authority.
- Migration test artifacts, runner code and executable files require a later
  implementation authority.

## 82. Recovery-readiness matrix

| Scenario | Detection | Automatic action | Operator/recovery path | Non-recoverable condition |
|---|---|---|---|---|
| Unexpected shutdown | SQLite/WAL recovery plus running ScanRun/MigrationAttempt on startup | SQLite rolls back uncommitted pages; mark interrupted scan non-complete; keep writes disabled during validation | Review safe diagnostics; rerun scan after gates pass | Committed files fail integrity and no valid recovery set exists. |
| Power loss | WAL/journal recovery, quick_check, terminal/current/audit agreement | Recover last committed transaction only; checkpoint after validation | Restore matching recovery set if checks fail | DB/history/secret recovery set all unavailable or inconsistent. |
| Partial transaction | Transaction rollback and absent commit/audit/version marker | Roll back whole UoW; idempotent retry only after reread | Investigate repeated storage failure | Partial state exists outside transaction and cannot be reconciled from audit/backup. |
| WAL recovery issue | WAL mode/checkpoint state and integrity checks | Do not copy/discard WAL blindly; open recovery validation | Use SQLite-consistent backup/restore tooling under later implementation procedure | Main/WAL pair corrupt with no valid backup. |
| Database corruption | quick_check/integrity_check/FK/digest/application_id failure | Enter read-only recovery/fail-closed mode | Restore validated DB+secret+provenance/config set or governed forward repair | Required collision/audit/history lost with no trusted copy. |
| Bundle mismatch | Bundle digest/reference/contract compatibility differs from VersionState/decision | Deactivate bundle provider; preserve DB/current identity | Restore/reselect validated referenced bundle or make new governed compatibility decision | Bundle is unavailable and operation requires its non-reconstructable historical semantics. |
| Schema mismatch | version_state/migration_state/user_version or supported-range mismatch | Refuse writes/startup activation | Compatible implementation, governed migration or validated restore | No compatible implementation/migration/backup exists. |
| Secret-store loss | SecretProvider lookup/generation/integrity validation fails | Block identity derivation/activation; never regenerate | Restore exact protected secret generation with matching recovery set | Secret irretrievably lost while stable identities/history must continue. |
| Interrupted migration | Running/incomplete attempt, version/checksum or post-check mismatch | Keep activation blocked; rollback transaction if uncommitted | Restore pre-migration set or apply governed forward-fix after review | Transformation committed inconsistently and no valid restore/repair evidence exists. |
| Interrupted scan | ScanRun remains running/nonterminal or lacks complete capability proof | Terminalize through recovery as failed/interrupted audit; preserve all current projections | Start a new scan with a new attempt/idempotency identity | Required prior current/history state is corrupt independently of scan interruption. |

Automatic recovery never changes installation scope, secret generation, public
reference, clone classification or removal state by inference.

## 83. Repository readiness verification

| Owner | Exclusive write authority | Read/transaction/constraint responsibility | Recovery readiness | Status |
|---|---|---|---|---|
| LogicalInstallationRepository | Installation/context/clone/activation/declaration/provenance | Bootstrap/clone/activation; context/scope/idempotency/FK constraints | Matching recovery-set restoration and active-context validation | READY |
| CollisionRegistryRepository | Registry/registration | Atomic collision UoW; both uniqueness domains; retained history | Fail closed; validated registry restore | READY |
| EntityRepository | Entity/current/event | Entity/lifecycle/removal; state/FK/idempotency constraints | Rebuild current only from retained event/evidence | READY |
| RelationshipRepository | Relationship/current/event | Tuple/source/target/continuity UoW | Rebuild current from retained events/identity refs | READY |
| ScanRunRepository | Run/capability outcomes | Start/completion/terminal/completeness | Recover interrupted as non-complete | READY |
| ObservationRepository | Observation/subject links | Normalization/privacy/taxonomy/retention | Restore A–F; regenerate/discard by class | READY |
| CompatibilityDecisionRepository | Compatibility decisions | Closed result/version/bundle evaluation | New evaluation never rewrites history | READY |
| AuditRepository | Audit/evidence/subject links | Mandatory append/idempotency/reverse references | Immutable backup only | READY |
| VersionStateRepository | Version singleton | Startup/compatibility/migration current vector | Compatible migration/restore | READY |
| MigrationStateRepository | Migration state/attempts | Exclusive order/checksum/status/version advancement | Rollback, restore or governed forward-fix | READY |

No physical table has two write owners. Cross-owner reads and UoWs do not
transfer authority. Tagged links remain transaction-validated reference rows.

## 84. Official implementation roadmap

No batch is authorized until a new implementation authority is active.

| Batch | Scope | Required verification gate |
|---|---|---|
| Implementation Batch 1 — SQLite infrastructure | Connection factory, local path boundary, PRAGMA initialization/validation, secret-provider abstraction/adapters, schema metadata model, migration runner skeleton, integrity/recovery-mode foundation | Disabled/default behavior preserved; platform secret threat review; connection/PRAGMA/fault tests; no schema activation beyond authorized bootstrap. |
| Implementation Batch 2 — Physical schema | Author the eight ordered migrations for 25 tables/243 columns, 53 candidate keys, 57 FKs, 30 constraints and 18 index dispositions; append-only triggers; schema verifier | Clean bootstrap, migration checksum/replay/forward-version/corruption tests; deterministic schema fingerprint; no contract change. |
| Implementation Batch 3 — Repository and UoW foundation | Ten repository implementations, canonical error translation, serialized writer, ten UoWs, idempotency and recovery coordination | Unit/integration tests for every constraint/error/UoW, concurrency/busy rollback, mutation triggers and restart recovery. |
| Implementation Batch 4 — Identity and scan persistence | Installation/context, collision/entity/relationship, scan/observation/lifecycle/removal and audit integration behind disabled feature boundary | Complete/partial/failed scan matrices; zero absence inference; collision/clone/secret loss; history/audit immutability; baseline regression. |
| Implementation Batch 5 — Compatibility and operational readiness | Version/compatibility decisions, validated bundle references, backup/restore validation, diagnostics, performance/capacity and production-readiness evidence | Bundle mismatch/reload, migration/restore, privacy/secret audit, bounded workload/query-plan tests, full regression, clean-copy/determinism review. |

Each batch is separately reviewable and may stop on an architecture conflict.
Implementation must not activate contract 2.0.0, confirmation/scoring/UI or
unrelated runtime behavior.

## 85. Implementation-readiness assessment

| Area | Classification | Evidence / note |
|---|---|---|
| Conceptual completeness | READY | 10 roots, 12 owned entities and exclusive value/reference/view ownership. |
| Logical completeness | READY | 25 relations, 53 candidate keys, 30 constraints, 26 mappings and 3NF policy. |
| Physical completeness | READY | 25 tables, 243 columns, 57 FKs, 18 indexes and full physical catalogue. |
| Repository readiness | READY | Ten exclusive owners and error/transaction responsibilities. |
| Migration readiness | READY | Eight phases plus authoring/checksum/replay/repair policy. |
| SQLite readiness | READY | Single writer, PRAGMA set, constraint/trigger/index mapping and escalation gate. |
| Recovery readiness | READY | Ten-scenario matrix and consistent recovery unit. |
| Consistency/invariants | READY | All LC-001–030 have primary enforcement and test duty. |
| Ownership/bounded contexts | READY | Operational, secret, HASK, HUDD, config/output/cache remain separate. |
| Secret-provider implementation | READY WITH NOTES | Abstract contract is complete; concrete Linux/container adapter selection and threat review are required in Implementation Batch 1. |
| Executable migration/test assets | READY WITH NOTES | Intentionally absent under DB-001; future implementation authority creates and validates them. |
| Production activation | READY WITH NOTES | Requires all five batches, independent verification and a later activation authority; not granted here. |

There are no `NOT READY` architecture areas. Notes are implementation/governance
gates, not missing database design.

## 86. Final consistency and prerequisite audit

| Audit item | Verified state |
|---|---|
| Aggregate roots | 10, each once |
| Owned conceptual entities | 12, each once |
| Logical relations / physical mappings | 25 / 25, one-to-one plus three declared associations |
| Physical columns | 243 catalogued |
| Candidate keys | 25 primary + 28 alternate = 53 represented |
| Fixed foreign keys | 57 restrictive references |
| Constraints | LC-001–LC-030 all owned/enforced/testable |
| Indexes | 18 named purpose/cost/disposition records |
| Migration reachability | Eight phases, each with prerequisite/checkpoint/recovery |
| Repository ownership | Ten exclusive write owners |
| Units of work | Ten physical transaction mappings |
| Retention | Twelve taxonomy classes each have one policy; seven policy kinds used |
| Current/history/audit | Separate projections, immutable events/observations/audit |
| Bundle/seed boundary | HASK bundle read-only; masterlists remain offline research seeds |
| Secret boundary | Secret bytes absent from all 25 tables and public output |
| HUDD | Separate read-only knowledge database |
| Canonical installation identity | LogicalInstallation only |
| Collision authority | One installation-wide CollisionRegistry with retained registrations |
| LifecycleHistory | Derived ordered view only; no table or duplicate authority |
| `source_ref` / `target_ref` | Accepted entity opaque reference / frozen target semantics preserved |
| Contract/baseline | Contract 1.0.0 active; 2.0.0 inactive; DF-002 baseline unchanged |

Implementation prerequisites:

1. a new active implementation authority explicitly permitting HADocs code,
   dependency/configuration, executable migrations and tests;
2. concrete Windows and Linux/container SecretProvider adapter selection,
   threat review and protected backup procedure;
3. approved filesystem path/configuration and upgrade/backup operational policy;
4. frozen migration checksum manifest/fingerprint procedure;
5. preservation/preflight of the existing HADocs dirty baseline; and
6. independent review gates after each implementation batch.

## 87. DB-001 final report and completion assessment

### Executive summary and maturity

DB-001 progressed from repository inventory through bounded technology and
ownership decisions, retention taxonomy, canonical aggregate model, 3NF logical
relations and complete documentation-only SQLite physical design. The result is
an **implementation-ready database architecture** with deterministic identity,
current/history separation, fail-closed recovery and explicit implementation
governance.

Architecture maturity: **FOUNDATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED**.

### Remaining risks

- Concrete Linux/container secret protection is platform-dependent and must be
  selected/tested before implementation completion.
- SQLite remains bounded to one local serialized writer and the documented
  capacity/transaction assumptions; crossing the escalation gate requires
  governed reassessment.
- Executable migrations, triggers and repositories may expose implementation
  defects; they must stop rather than reinterpret this architecture.
- Backup correctness depends on atomic coordination with secret/provenance and
  WAL-aware tooling not yet implemented.
- Tagged subject references require comprehensive transaction validation because
  SQLite cannot express polymorphic FKs directly.

### Completion

DB-001 satisfies its charter and completion condition:

- the sole required foundation document exists and is complete;
- all identity-bearing concepts have a persistence location or external boundary;
- current state and immutable history are separate;
- schema and public contract versions are separate;
- genuine open architecture decisions are closed;
- implementation prerequisites and batches are explicit; and
- no production/runtime/schema artifact was created.

**DB-001 status: COMPLETE.**

**Implementation authorization recommendation:** after an explicit governance
transition, authorize Implementation Batch 1 only, with the existing default-
disabled behavior and baseline-preservation preflight. Do not authorize all five
batches as one undifferentiated change.

DB-001 remains the sole pointer-selected authority until a separate governance
transition updates ACTIVE, the governance index/state and durable status records.
This document's completion does not itself perform that transition.
