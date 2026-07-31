# IM-001 Batch 3 Correction Authority-Conflict Report

## Outcome

`CORRECTION_INCOMPLETE`

The bounded correction cannot begin under the current authority. No correction
code, tests, schema, migration, architecture, contract or governance artifact
was modified.

## Authority preflight

- Active authority: `IM-001`.
- Implementation authorization: `TRUE`.
- Implementation scope: `IM-001-BATCH-3`.
- Batch 3: `AUTHORIZED_NOT_STARTED` in repository governance.
- Batch 4: `UNAUTHORIZED`.
- Registered physical-schema SHA-256:
  `623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673`.
- DB-001 SHA-256:
  `676e5cca648bf894eb69c1329371819e272fade44eba5ff9130fc3d1d0491e79`.
- DB-002 SHA-256:
  `6d754c18f3a1172c71e9b5be0d701535ff84598b8792ea61966e9a965e54b6b9`.
- ACR-001 SHA-256:
  `9443b1cf4dee94ca642fe46be40d05e4bd00b76de2d16e066bd02798b06f9b76`.

## Conflict A — required review evidence is not repository-authoritative

The correction preflight requires the independent Batch 3 review report as an
authoritative input. No Batch 3 independent-review artifact is present in
`D:\HA-Stability-Knowledge` or
`C:\HomeAssistantDocs\docs\integration\hask_runtime`.

G-002 states that conversation history and cached context are never authority.
The findings restated in the correction request therefore cannot substitute for
the missing repository report or prove that they are registered findings.

Required resolution: register the completed independent review byte-for-byte as
a repository-authoritative artifact before a correction increment consumes it.

## Conflict B — cross-restart idempotency requires prohibited persistence

### Frozen DB-001 requirement

DB-001 assigns idempotency identity to the persisted aggregate rows and their
scoped alternate keys, including `scan_run`, `observation`,
`compatibility_decision`, `audit_record`, `clone_decision`,
`activation_outcome`, lifecycle events and `migration_attempt`. DB001-D-022
defines natural/idempotency candidates as alternate unique keys. LC-017 and
LC-025 require persisted run/audit idempotency behavior, and the ten physical
Units of Work require equivalent retries to return the prior result while
conflicting retries fail.

DB-002 likewise states that idempotency returns the existing row without
issuing `UPDATE`.

These requirements make cross-transaction, cross-process and cross-restart
comparison dependent on reading the already persisted aggregate row and, on the
first successful claim, atomically creating the aggregate/audit result protected
by its frozen alternate key.

### Frozen schema allocation

The registered 25-table schema contains no standalone transaction-
infrastructure idempotency ledger. Adding such a table, column, index or
migration is prohibited and would change the registered physical-schema
checksum.

### Active IM-001 boundary

The active IM-001 authority states that Batch 3 does not authorize runtime or
business persistence and that identity, lifecycle, audit, scan and operational
persistence remain reserved for Batch 4. It also prohibits normal runtime calls
to repository methods during Batch 3.

### Incompatibility

The requested acceptance criterion requires executable cross-restart and
cross-process idempotency now. Satisfying it through the frozen schema requires
the exact runtime/business row writes reserved for Batch 4. An in-memory map or
an abstract interface would not satisfy restart/process durability. A new
infrastructure ledger would violate the frozen schema. Consequently no permitted
Batch 3 implementation can meet B3R-F-003 as requested.

## Affected correction findings

| Finding | Status | Reason |
|---|---|---|
| B3R-F-001 | NOT STARTED | Mandatory independent-review source is absent. |
| B3R-F-002 | NOT STARTED | Mandatory independent-review source is absent. |
| B3R-F-003 | AUTHORITY CONFLICT | Durable idempotency requires Batch 4-owned persistence or a prohibited schema change. |
| B3R-F-004 | NOT STARTED | Correction batch stopped before code changes. |
| B3R-F-005 | NOT STARTED | Tests cannot be corrected before the authority conflict is resolved. |

## Required governance resolution

Before correction can resume, governance must:

1. register the independent Batch 3 conformance review as immutable,
   repository-authoritative evidence; and
2. resolve the Batch 3/Batch 4 allocation for persisted idempotency without
   weakening DB-001, inventing an in-memory substitute or modifying the frozen
   schema implicitly.

Possible resolution categories are not selected here. Selecting one requires a
separately authorized governance or architecture determination because the
current correction instruction explicitly forbids improvisation.

## Preservation statement

- Batch 3 remains open and is not marked complete.
- Batch 4 remains unauthorized.
- No implementation correction was made.
- No runtime or business persistence began.
- DB-001, DB-002, DB-002A, DF-002 and the registered physical schema remain
  unchanged.
