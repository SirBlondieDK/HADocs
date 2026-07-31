# R-004 Independent Architecture Review Report

## Result

**FAIL**

CA-001 cannot yet be accepted because one MAJOR finding leaves collision-detection scope to implementation. The cryptographic derivation itself is correct and all published vectors reproduce, but R-004's rules require FAIL for any MAJOR finding or unresolved architectural ambiguity.

## Review scope

R-004 independently reviewed every completed CA-001 deliverable against:

- DF-002 and its frozen producer, privacy, relationship and version models;
- AI-001 as immutable prerequisite evidence;
- all five R-003 findings, with CA-001 correctly limited to the cryptographic R003-F-001 defect;
- CA-001's own requirements, decision gates and seventeen-item open-decision inventory.

The review covered internal consistency, HMAC-SHA-256 correctness, canonical bytes, output length, secret lifecycle, installation and kind separation, privacy, failure behavior, migration, coexistence, version handling, rejected alternatives and test-vector reproducibility.

## Methodology

1. Reloaded permanent governance and validated the active state before accessing the review output boundary.
2. Inventoried the R-004 directory under G-002; no prior deliverables existed.
3. Read all ten CA-001 documents in full and built requirement-to-specification traceability.
4. Compared inherited claims with DF-002, AI-001 and R-003 rather than accepting CA-001's summaries alone.
5. Reconstructed every normative message component from prose in two independent runtimes.
6. Recomputed all six positive vectors and both version/domain verification vectors.
7. Audited each CA001-D-001 through CA001-D-017 for closure.
8. Classified defects without editing or replacing the reviewed architecture.

## Reviewed documents and conclusion

| Document | Review conclusion |
|---|---|
| `CA-001_EXISTING_AUTHORITY.md` | Correctly preserves DF-002, isolates R003-F-001 and does not claim activation. |
| `CA-001_REQUIREMENTS.md` | Correctly captures the keyed privacy, determinism, lifecycle, compatibility and verification gates. |
| `CA-001_OPEN_DECISIONS.md` | Complete decision inventory; D-015 exposes the unresolved detection-scope requirement found by R-004. |
| `CA-001_DECISION_CRITERIA.md` | Fair mandatory gates and comparative criteria; no hidden primitive preference. |
| `CA-001_ARCHITECTURE_ALTERNATIVES.md` | Eligible alternatives are described fairly with security, dependency, migration and operational tradeoffs. |
| `CA-001_RECOMMENDED_ARCHITECTURE.md` | HMAC-SHA-256 recommendation is technically justified; entropy wording is imprecise (MINOR). |
| `CA-001_NORMATIVE_SPECIFICATION.md` | Cryptographic bytes are complete and unambiguous; collision response lacks mandatory detection scope (MAJOR). |
| `CA-001_SECRET_LIFECYCLE.md` | Generation, canonical secret encoding, startup validation, backup, rotation and fail-closed behavior are coherent. |
| `CA-001_MIGRATION_AND_RECOVERY.md` | Correctly prevents silent regeneration, aliasing, mixed generations and silent identity reassignment. |
| `CA-001_TEST_VECTORS.md` | Every published result reproduces twice; an explicit scope-only separation vector is absent (MINOR). |

## Compatibility assessment

### DF-002

The proposal restores the frozen secret-local-material privacy property, preserves fail-closed behavior and does not alter the active baseline or contract. Compatibility is conceptually satisfied for the cryptographic defect, subject to resolving R004-F-001 before acceptance.

### AI-001

CA-001 clearly replaces only AI-001's unkeyed `ref1_` cryptographic proposal with a distinct `refh1_` format and does not silently alias them. It preserves AI-001's public installation-scope grammar as an authenticated input without treating that public scope as the secret.

### R-003

CA-001 addresses R003-F-001. It correctly leaves clone classification, relationship `source_ref`, removal semantics and major-contract-version correction outside its scope. It does not falsely resolve or weaken R003-F-002 through R003-F-005.

## Cryptographic assessment

- Primitive use: PASS.
- Full 256-bit output/no truncation: PASS.
- Canonical framing and byte order: PASS.
- NFC/UTF-8 and length framing: PASS.
- Domain separation: PASS.
- Reference-kind separation: PASS.
- Test-vector reproducibility: PASS.
- Secret validation and fail-closed behavior: PASS.
- Rotation, recovery and version boundaries: PASS.
- Collision-detection architecture: FAIL (R004-F-001).

## Findings

- `R004-F-001` — **MAJOR** — collision detection scope remains undefined.
- `R004-F-002` — **MINOR** — entropy terminology overstates what startup validation can establish.
- `R004-F-003` — **MINOR** — no normative scope-only separation vector.

Complete evidence and consequences are recorded in `R-004_FINDINGS.md` and `R-004_VALIDATION_EVIDENCE.md`.

## Acceptance recommendation

**CA-001 cannot be accepted in its current form.**

The blocker is narrow: CA001-D-015 must be resolved by separately authorized architecture correction and independently re-reviewed. R-004 does not prescribe or implement that correction. The two MINOR findings do not independently block acceptance, but should be dispositioned by the authority that handles the MAJOR finding.

No Design Freeze, AI-002 resumption, contract change or implementation is authorized by this report.

