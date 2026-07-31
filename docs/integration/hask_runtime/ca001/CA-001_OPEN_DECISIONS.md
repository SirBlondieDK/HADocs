# CA-001 Open Decisions

## Status

Every item below is OPEN. This document records the decision surface and does not resolve it.

| ID | Open architecture decision | Required future output |
|---|---|---|
| CA001-D-001 | Keyed cryptographic primitive | Exact standardized construction and parameter set |
| CA001-D-002 | Secret representation | Conceptual type, exact byte length, encoding and minimum entropy |
| CA001-D-003 | Secret creation | Generation authority, source requirements, creation timing and validation |
| CA001-D-004 | Domain separation | Exact purpose labels and separation between reference kinds or identity uses |
| CA001-D-005 | Input model | Exact fields, order, normalization, byte encoding and length framing |
| CA001-D-006 | Installation scoping | Exact participation of private secret and public installation scope |
| CA001-D-007 | Output representation | Prefix, digest encoding, full/truncated length and validation grammar |
| CA001-D-008 | Reference-kind separation | Entity, device, area and label handling and cross-kind collision prevention |
| CA001-D-009 | Persistence boundary | Storage abstraction, access restriction and durability requirements |
| CA001-D-010 | Backup and migration | Portability, restoration and preservation of derivation context |
| CA001-D-011 | Rotation | Authorized triggers, prohibited triggers and observable identity consequences |
| CA001-D-012 | Loss and corruption | Detection, fail-closed behavior, recovery authority and historical continuity |
| CA001-D-013 | Compatibility | Existing `ref1_` treatment, coexistence, migration and public-byte impact |
| CA001-D-014 | Format version | Cryptographic format namespace independent of active contract activation |
| CA001-D-015 | Collision response | Detection scope, failure boundary and relationship consequences |
| CA001-D-016 | Normative vectors | Synthetic input set, exact bytes and reproducibility method |
| CA001-D-017 | Threat model | Protected adversary capabilities, explicit non-goals and residual risks |

## Dependency order

```text
Threat model and inherited requirements
  → primitive and secret parameters
  → domain separation and canonical input bytes
  → output and format version
  → lifecycle, rotation and recovery
  → compatibility and migration
  → normative synthetic vectors
```

No item is an implementation default when it changes public identity bytes, stability, privacy or migration behavior. CA-001 must record a blocker rather than leave such a choice to implementation.

