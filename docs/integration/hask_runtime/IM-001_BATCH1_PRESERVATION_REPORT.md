# IM-001 Batch 1 Preservation Report

## Decision

PASS. The preservation gate completed before the first IM-001 implementation
write on 2026-07-25.

## Governance and frozen inputs

- Active authority: `IM-001`.
- Authorized scope: Batch 1 SQLite infrastructure only.
- Batches 2–5: not authorized by this execution.
- General implementation baseline: DF-002.
- Frozen database baseline: `DB-001_HASK_DATABASE_FOUNDATION.md`.
- Expected and observed DB-001 SHA-256:
  `676e5cca648bf894eb69c1329371819e272fade44eba5ff9130fc3d1d0491e79`.
- Active public contract: `hadocs-generic-metadata 1.0.0`.
- Proposed contract 2.0.0: inactive.

## HADocs starting state

- Branch: `main`.
- HEAD: `590cc33a9762c4d22699f20c60d136ef2c4de00c`.
- Existing tracked modifications: 8.
- Existing untracked files: 1,884.
- Canonical sorted modified/untracked file inventory SHA-256:
  `a90522e1210ccef10974c1a2b46221150e166b09478a82f34399daeb9edc9561`.
- Existing tracked and untracked files were preserved. No reset, clean, stash,
  restore, checkout, commit, or deletion was performed.

The approved dirty-baseline and completed pilot/PI1 manifests remain present.
Their historical reports record zero unexpected mismatch at their respective
freeze points. Later governed additions are preserved and were not
misclassified as baseline drift.

## Existing implementation audit

No HASK operational SQLite package, schema, table, migration artifact,
repository, or runtime business persistence existed before Batch 1. The older
general HADocs database and the separate HUDD database remain distinct and
unchanged.

## Baseline tests

The complete suite passed before implementation: **251 passed** using Python
3.14, explicit `src` import path, disabled pytest cache, and an isolated
temporary directory. An earlier Python 3.9 invocation failed during collection
because that interpreter is below the project's declared Python requirement;
no tests ran in that invocation and no repository file was changed.
