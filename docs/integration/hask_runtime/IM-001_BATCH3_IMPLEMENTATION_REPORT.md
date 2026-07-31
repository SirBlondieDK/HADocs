# IM-001 Batch 3 Implementation Report

## Result

IM-001 Batch 3 repository infrastructure is implemented with **PASS** and is
recommended for formal completion. No runtime or business persistence was
implemented. Batch 4 responsibilities were not started.

## Preservation

| Baseline | SHA-256 | Result |
|---|---|---|
| DB-001 | `676e5cca648bf894eb69c1329371819e272fade44eba5ff9130fc3d1d0491e79` | PASS |
| DB-002 | `6d754c18f3a1172c71e9b5be0d701535ff84598b8792ea61966e9a965e54b6b9` | PASS |
| ACR-001 | `9443b1cf4dee94ca642fe46be40d05e4bd00b76de2d16e066bd02798b06f9b76` | PASS |
| Physical schema | `623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673` | PASS |

No SQL, migration, table, column, key, constraint, index, trigger, view,
architecture, contract or governance artifact changed.

## Repository inventory and ownership

| Frozen owner | Exclusively owned tables |
|---|---|
| LogicalInstallationRepository | logical_installation, installation_context, authoritative_declaration, protected_provenance_reference, clone_decision, activation_outcome |
| CollisionRegistryRepository | collision_registry, identity_registration |
| EntityRepository | entity, entity_current_state, entity_lifecycle_event |
| RelationshipRepository | relationship, relationship_current_state, relationship_lifecycle_event |
| ScanRunRepository | scan_run, scan_capability_outcome |
| ObservationRepository | observation, observation_subject_link |
| CompatibilityDecisionRepository | compatibility_decision |
| AuditRepository | audit_record, audit_evidence_link, audit_subject_link |
| VersionStateRepository | version_state |
| MigrationStateRepository | migration_state, migration_attempt |

Exactly ten repositories cover all 25 frozen tables once. No owner was added,
removed, split or merged. Repository lifetime is one Unit of Work.

## Repository boundary and dependency injection

- `RepositoryContract` exposes only immutable ownership metadata.
- Concrete adapters keep SQLite private.
- No repository exposes public read or write methods in Batch 3.
- `RepositoryRegistry` rejects duplicate or incomplete owner sets.
- `RepositoryFactory` resolves all ten owners deterministically for one active
  Unit of Work.
- The transaction manager does not expose its raw SQLite connection.
- Business code therefore has no Batch 3 persistence entry point.

## Transaction validation

- One non-blocking process-local writer lock serializes Units of Work.
- Every transaction begins `IMMEDIATE` through the transaction boundary.
- Successful scopes commit; exceptional scopes roll back.
- Nested Units of Work are rejected.
- Repository resolution is valid only while its Unit of Work is active.
- Factory failure after transaction acquisition rolls back and releases the
  writer.
- SQLite failures are translated before crossing the infrastructure boundary.

The bounded retry policy has three attempts with deterministic delays of 25,
57 and 119 ms and a 500 ms total ceiling. Only busy/locked concurrency failures
are retried. Integrity, storage and constraint errors are not blindly retried.

## Canonical error translation

All twelve frozen DB-001 categories are represented: `NOT_FOUND`,
`ALREADY_EXISTS`, `CONSTRAINT_VIOLATION`, `VALIDATION_FAILURE`,
`CONCURRENCY_CONFLICT`, `STORAGE_FAILURE`, `CORRUPTION_DETECTED`,
`MIGRATION_FAILURE`, `SECRET_UNAVAILABLE`, `BUNDLE_MISMATCH`,
`VERSION_INCOMPATIBLE` and `IDEMPOTENCY_CONFLICT`.

SQLite integrity, lock/busy, corruption and storage failures translate to safe
repository errors without returning raw SQLite exceptions.

## Idempotency and recovery validation

- Transaction-local idempotency uses canonical sorted JSON and SHA-256.
- Equivalent normalized intent is a repeat; differing intent under the same
  scoped key raises `IDEMPOTENCY_CONFLICT`.
- No idempotency state is persisted in Batch 3.
- Recovery states are `NORMAL`, `RECOVERY_REQUIRED` and `VALIDATING`.
- Transactions fail closed outside `NORMAL`.
- Failed validation returns to `RECOVERY_REQUIRED`; successful validation alone
  returns to `NORMAL`.
- Commit/rollback storage failure enters recovery-required state.

## Append-only responsibility

Batch 2 SQLite triggers remain the primary append-only enforcement. Batch 3
adds no mutation API and exposes no repository write method, so it cannot bypass
those triggers. Semantic authorization and audit orchestration remain reserved
for later, separately authorized persistence work.

## Tests

- New Batch 3 tests: 18.
- Targeted database tests: **45 passed**.
- Complete HADocs suite: **296 passed**.
- Ownership/registration: PASS.
- DI/factory resolution: PASS.
- Commit/rollback/nested protection: PASS.
- Canonical error translation: PASS.
- Idempotency/recovery coordination: PASS.
- Schema fingerprint preservation: PASS.

## Files

Created:

- `src/hadocs/hask_database/repository_contracts.py`
- `src/hadocs/hask_database/repositories.py`
- `src/hadocs/hask_database/coordination.py`
- `src/hadocs/hask_database/transactions.py`
- `tests/test_hask_database_repositories.py`
- `docs/integration/hask_runtime/IM-001_BATCH3_CONFORMANCE.json`
- this report

Modified:

- `src/hadocs/hask_database/errors.py`
- `src/hadocs/hask_database/__init__.py`

## Scope conclusion

Runtime, business, bundle, item, identity, lifecycle, audit, scan, operational
and entity persistence remain zero. No normal runtime path is connected to the
repository infrastructure. Batch 4 remains unauthorized.
