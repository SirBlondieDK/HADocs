# HASK Preview release-candidate report

Batch: `HADOCS-HASK-PREVIEW-001`

Date: 2026-07-30

Workspace: `C:\HomeAssistantDocs`

## 1. Recovery checkpoint

- Archive: `C:\Users\sirbl\HADocs-before-hask-preview-20260730-081229.zip`
- Size: 63,665,460 bytes
- Entries: 6,089
- Uncompressed content: 313,640,296 bytes
- SHA-256: `B50422AFBBB1FAB39A16404A41BBFE47651170A31E3388B8B96E4AD2AA68E537`
- Full ZIP CRC/read-back: passed
- The permission-restricted `.pytest_tmp` directory was represented as a
  directory entry; Windows exposed no readable content.

The checkpoint excludes `.git` internals but includes all readable worktree
source, tests, documentation, migrations, configuration, untracked product
work, Issue #29 changes, historical evidence, local data, and generated
artifacts needed for recovery.

## 2. Pre-cleanup inventory

- Git status entries: 184
- Tracked modified paths: 149
- Untracked files: 341 (35 collapsed status entries)
- Staged paths: 0
- Ignored files: 3,041
- Pytest temporary directories: 23, plus `.pytest_cache`
- Generated SQLite/database files: 349
- Bytecode files: 318
- `__pycache__` directories: 36
- `build`: 197 files / 19,277,869 bytes
- `dist`: 1,090 files / 36,355,249 bytes
- `output`: 285 files / 6,643,206 bytes
- No merge, rebase, cherry-pick, revert, or bisect state existed.

The exact machine-readable classification was fixed before removal at
`C:\Users\sirbl\HADocs-hask-preview-cleanup-manifest-20260730-081419.json`
(SHA-256 `98556494F54C87CC3263FB4BBCF6DB80CCC5BF59F54E59FC31AC358CDFD8479B`).

## 3. Cleanup classification

- **Group A — required product source:** `src/hadocs`, entry points, App,
  Docker, installer, and product tools.
- **Group B — required tests/fixtures:** `tests` and synthetic fixtures.
- **Group C — required runtime resources:** eight operational migrations,
  HUDD data/schema/migration, web assets, and the validated HASK bundle.
- **Group D — current documentation:** top-level product documents, current
  guides, architecture decisions, and canonical integration status.
- **Group E — historical evidence:** `archive`, historical integration reports,
  governance evidence, and deferred metadata-collector source.
- **Group F — local user data:** root local configuration, device overrides,
  and generated reports.
- **Group G — reproducible output:** build, distribution, and egg-info output.
- **Group H — temporary artifacts:** pytest directories, bytecode caches,
  generated test databases, WAL/SHM files, and test output.
- **Group I — unknown/preserve:** `.agents` and any item without authoritative
  classification.

## 4. Exact removals

Direct deletion was denied by execution policy, so every accessible removal was
performed as a recoverable move with its repository-relative path preserved in:

- `C:\Users\sirbl\HADocs-cleanup-quarantine-20260730-081537`
- `C:\Users\sirbl\HADocs-cleanup-quarantine-20260730-081537-2`

Removed from the repository:

- `build/` — 197 files / 19,277,869 bytes
- `dist/` — 1,090 files / 36,355,249 bytes
- `src/hadocs.egg-info/` — 6 files / 9,478 bytes
- `output/` — 285 files / 6,643,206 bytes
- `config.json` and `device_overrides.json`
- `.pytest_cache/`
- all 22 accessible `.pytest_tmp_*` directories
- all 36 `__pycache__` directories and all 318 `.pyc` files
- 348 generated SQLite/database files, including test WAL/SHM companions

The only remaining cleanup path is `C:\HomeAssistantDocs\.pytest_tmp`, which
Windows denies for listing, ACL inspection, moving, and deletion. It cannot
affect Git status or packaging and contains no readable source.

## 5. Preserved local user data

Verified backup:
`C:\Users\sirbl\HADocs-local-data-backup-20260730-081444`

- `config.json`: 205 bytes; SHA-256
  `586D60A02BFDFA07FEBD1D0D640C20B77777D264611824E3B8C1970D1CCA41EC`
- `device_overrides.json`: 2,337 bytes; SHA-256
  `FC1A26F29D8EEB5542B45CBCD1741CF21402476CB5709926745A678A83960E5E`
- `output/`: 285 files / 6,643,206 bytes; deterministic tree SHA-256
  `DAB6DB883CBD1380FDA2A82146A84E08B2251299548F991E73F04C9E93D55ADA`
- Total verified: 287 files / 6,645,748 bytes
- Backup-manifest SHA-256:
  `3C1BA4CAB708BFC97408DB66B4716BB3B84FD0362B3F3852B5AB80B073D3CFEC`

Source and copy size/SHA-256 comparisons passed before removal. All four local
configuration locations and runtime output categories are ignored. No secret,
credential, URL, identifier, UUID, or private value was printed.

## 6. Documentation classification

`docs/README.md` is the concise navigation authority. It separates current
product documentation, current HASK Preview documentation, historical
implementation evidence, deferred work, and obsolete pointer documents retained
for traceability. `docs/integration/HASK_INTEGRATION_STATUS.md` remains the
canonical product boundary. Historical governance does not control current
runtime behavior. No integration-history family was bulk-deleted or moved.

## 7. Version-authority correction

The existing documented desktop runtime module, `hadocs.version`, is now the
single authority:

- SemVer release authority: `0.15.0`
- Display/preview channel: `0.15.0-rc1`
- Wheel-normalized metadata: `0.15.0rc1`

`pyproject.toml` derives wheel metadata dynamically from that module. CLI,
GUI/about dialog, source execution, installed wheel, frozen executable, and
HASK minimum-version negotiation use the same authority. The previous HASK
hardcode and knowledge-export version literals were removed. Malformed or
unavailable bundle version metadata fails closed.

## 8. Source HASK bundle identity

Read-only source: `D:\HA-Stability-Knowledge\dist\hadocs`

- Files: 14 generated JSON files
- Bytes: 4,833,291
- Deterministic tree SHA-256:
  `B9C35715EDD257C9D0FB7F16C71A2117D4CE0587C4176D695B8D96FC90F10011`
- Contract: `hask-hadocs` `1.1.0`
- Knowledge content: `0.2.0`
- Knowledge schema: `2.0.0`
- Minimum HADocs: `0.15.0`
- Manifest aggregate artifact SHA-256:
  `1df827f372170e1946bd43be54dddbf7355d2e4f4ad6f2f816d7423bd2643a47`

The supplied authoritative baseline (633 records, 169 sources, 539 claims,
1,805 semantic relationships; inventory SHA-256
`9fa394b5de051c0ea1a66fdb0fb6a560d77736ed332190e42e15d5f375825f20`)
is recorded as provenance only. Those authoritative workspace counts are not
misrepresented as executable matchers or consumer-manifest totals.

## 9. Copied bundle identity

Product resource:
`src/hadocs/knowledge/hask_bundle/0.2.0/`

Exact files:

- `manifest.json`
- `applicability.json`
- `competing_causes.json`
- `conflicts.json`
- `diagnostic_scenarios.json`
- `evidence_catalog.json`
- `evidence_matchers.json`
- `known_gaps.json`
- `platform_index.json`
- `provenance.json`
- `readiness.json`
- `recommendations.json`
- `root_cause_candidates.json`
- `verification_paths.json`

The copied tree is byte-identical to the source: 14 files, 4,833,291 bytes,
tree SHA-256
`B9C35715EDD257C9D0FB7F16C71A2117D4CE0587C4176D695B8D96FC90F10011`.

## 10. Bundle validation

Validation passed for manifest presence, exact contract name, contract version,
knowledge versions, minimum HADocs version, required artifact set, every
per-artifact SHA-256, aggregate SHA-256, typed artifact form, global duplicate
IDs, readiness-platform duplicate IDs, internal references, source references,
relationship targets, and consumer compatibility.

Validated consumer coverage contains 1,983 artifact items:

| Artifact | Items |
|---|---:|
| applicability | 539 |
| competing causes | 57 |
| conflicts | 9 |
| diagnostic scenarios | 57 |
| evidence catalog | 731 |
| evidence matchers | 25 |
| known gaps | 40 |
| platform index | 105 |
| provenance | 169 |
| readiness | 105 |
| recommendations | 61 |
| root-cause candidates | 24 |
| verification paths | 61 |

Only the 25 matcher records are matcher artifacts; the report does not claim
that every record is executable. Checksum-only trust remains explicit; publisher
signature verification is not implemented.

## 11. Preview architecture

`HaskPreviewService` resolves an explicit configured bundle first, the packaged
bundle second, and a visible unavailable state last. Invalid explicit
configuration fails closed without fallback. Runtime access is local and
read-only; no network call is implemented. Disabled report generation checks
only packaged/configured availability and does not validate, load, evaluate, or
open the operational database solely for Preview.

## 12. Shared Preview model

One frozen `HaskPreviewSnapshot` supplies web API, HTML report, CLI/package
smoke, and presentation rendering. It contains only bundle status, safe version
identity, checksum prefix, coverage counts, safe platform knowledge, public HASK
references, matcher identity/version, evidence categories, missing evidence,
conflict code, applicability, explanation, limitations, and the permanent
analytical-impact statement.

## 13. UI surfaces

- Web: `/hask-preview` and `/api/hask-preview`, plus overview/navigation link.
- Generated report: `hask_preview.json`, `hask_preview.html`, and a dedicated
  section in the main HTML report.
- Windows: independent Settings checkbox and the same report/web workflow.
- Home Assistant App: independent default-false option/environment mapping and
  web route through the existing ingress workflow.
- CLI/frozen verification: `hadocs hask-preview` emits only the shared redacted
  snapshot.

## 14. Classification semantics

The user-visible states are `SUPPORTED_CANDIDATE`, `INSUFFICIENT_EVIDENCE`,
`NOT_APPLICABLE`, `REJECTED_CONFLICT`, `BUNDLE_DISABLED`,
`BUNDLE_UNAVAILABLE`, and `BUNDLE_INVALID`. A HASK candidate is never labelled
confirmed, active finding, Root Cause, critical issue, recommendation, or score
improvement. UniFi and MikroTik remain insufficient-evidence candidates when
authoritative controller/API results are absent.

## 15. Privacy/redaction proof

Focused tests inject protected scan IDs, observation IDs, relationship IDs, and
protected subject references, then prove none enter canonical Preview JSON or
HTML. Preview DTOs contain no database IDs, raw entity/device/area/config-entry
IDs, installation scope, HMAC digests, credential handles, secrets, tokens, IPs,
configured URLs, or raw rows. Production-source secret-pattern scan: zero
matches. Synthetic fixtures only were used; no Home Assistant instance was
contacted.

## 16. Analytical isolation proof

For identical synthetic analytical DTOs, disabled and active Preview runs leave
findings, incidents, Root Causes, recommendations, severity, affected entities,
Health Score, Potential Health Score, estimated gain, device classifications,
and report analytical DTOs byte/structure identical. Generated HTML is identical
after replacing only the dedicated HASK Preview section. Preview has no score
field and receives no analytical mutation authority.

## 17. Issue #29 preservation

The centralized registry-disabled eligibility predicate remains authoritative.
The eight Issue #29 tests passed immediately after cleanup and again after
Preview implementation. Registry-disabled entities remain inventory/diagnostic
context only and cannot affect incidents, affected counts, Root Causes,
recommendations, severity, Health Score, Potential Health Score, or estimated
gain.

## 18. Tests

Environment: Python 3.14.3; pytest 9.1.1.

- Post-cleanup Issue #29: 8 passed
- Preview plus Issue #29: 32 passed
- Candidate/native/runtime integration focus: 66 passed
- Complete final suite: **480 passed, 0 failed, 14 skipped, 0 errors**
- AST parse: 274 source/test files
- Static import-cycle components: 0
- Import smoke: passed
- `git diff --check`: passed (line-ending notices only)
- Bash syntax for Home Assistant App startup: passed
- Database schema version: 8
- Schema SHA-256:
  `623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673`
- Schema deviations: 0; foreign-key violations: 0; integrity: `ok`

Tests default to an external process-owned temporary root, disable pytest's
repository cache provider, and suppress Python bytecode generation.

## 19. Packaging

Fresh wheel, built and installed from external staging:

- `hadocs-0.15.0rc1-py3-none-any.whl`
- Size: 939,767 bytes
- SHA-256:
  `0E1557F486BB06690C25415CA5310B9AB945ECEA1242FA13A51A8188EEBBA563`
- Entries: 211; CRC: clean
- Includes all 14 HASK JSON files, eight operational migrations, HUDD
  resources, Preview source and web assets
- Excludes tests, fixtures, caches, local configuration, device overrides,
  credentials, operational databases, reports, historical docs, authoritative
  HASK YAML/workspace, recovery archives, metadata collector, and build output
- Clean installed resource discovery: passed; clean run directory: empty

Fresh Windows PyInstaller build from external staging:

- `HADocs.exe` size: 6,342,662 bytes
- SHA-256:
  `1EBF2CDF9F327787A336638C308ECF8FE62F49747081E87B51FDAEF2D8EE31B3`
- Frozen tree: 1,043 files
- `--help`, `--version`, `database status`, and active packaged
  `hask-preview` smoke checks: exit 0
- Active frozen Preview: packaged source, contract `1.1.0`, valid
- HASK JSON files: 14; operational migrations: 8
- Missing HADocs module warnings: 0; forbidden packaged files: 0
- Clean frozen run directory: empty

Inno Setup is not installed on this host, so the existing installer definition
could not be compiled. Docker is not installed, so the Home Assistant App image
could not be built. Static App configuration tests, Docker/package definitions,
shell syntax, web routing, and the full regression suite passed.

Task-created test, wheel, install, and PyInstaller verification directories were
removed from their original external paths. Because direct recursive deletion
is denied by execution policy, their recoverable contents were consolidated
under `C:\Users\sirbl\HADocs-cleanup-quarantine-20260730-081537`.

## 20. Remaining limitations

- Publisher signature verification is deferred; the current trust state is
  checksum-valid/signature-not-implemented.
- Typed matchers remain bounded; authenticated UniFi/MikroTik controller probes
  and network logins are deferred.
- One inaccessible empty/unreadable `.pytest_tmp` path remains due Windows ACLs.
- Installer compilation and Docker image build require release hosts with Inno
  Setup and Docker respectively.
- HASK Knowledge Coverage Expansion/KX-024 was not started and requires separate
  authorization in `D:\HA-Stability-Knowledge`.

## 21. Worktree/Git state

- Branch remains `recovery/hask-snapshot-20260727`.
- HEAD remains `590cc33a9762c4d22699f20c60d136ef2c4de00c`.
- Staged paths: 0.
- Final `git status --short`: 1,278 entries — 1,084 deliberate tracked
  generated-output deletions, 154 tracked modifications, and 40 untracked
  entries.
- No commit, push, pull, fetch, merge, rebase, cherry-pick, reset, restore,
  checkout, clean, repository initialization, or history rewrite occurred.
- Tracked build/distribution files appear as deliberate cleanup deletions; all
  remain recoverable in the checkpoint and cleanup quarantine.
- Issue #29 and every legitimate pre-existing recovery path were preserved.

## 22. Exact next actions before commit

1. Human-review the unstaged source, tests, documentation, package-resource
   bundle, and deliberate generated-output deletions.
2. Resolve or remove the Windows-denied `.pytest_tmp` directory using an
   administrator-owned filesystem operation if desired.
3. Compile and smoke-test the Inno Setup installer on a release host.
4. Build/start the Home Assistant App image on a Docker-enabled release host.
5. Re-run the complete suite and package manifest checks if review changes any
   file.
6. Make one commit only after the product owner accepts the recovery diff.
7. Keep KX-024/HASK Knowledge Coverage Expansion paused until separately
   authorized in the HASK workspace.
