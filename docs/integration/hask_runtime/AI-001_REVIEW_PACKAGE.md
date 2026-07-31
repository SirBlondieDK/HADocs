# AI-001 Review Package

## Review target

R-003 should review the AI-001 proposal as one indivisible identity design. DF-002 remains authoritative until a later Design Freeze record supersedes it.

## Proposed decisions

1. Adopt persistent collector-managed installation scope with a non-exported raw UUIDv4 and deterministic public token.
2. Adopt byte-level length framing, NFC normalization, UTF-8 encoding, SHA-256, lowercase hexadecimal output, and explicit namespace versions.
3. Adopt closed Release 1 category-to-source-capability mappings.
4. Adopt category-aware canonical keys and installation-scoped observation IDs.
5. Adopt typed opaque references and deterministic relationship identifiers.
6. Adopt explicit rules for rename, removal, recreation, migration, duplicates, collisions, missing data, and invalid input.
7. Retain contract version `1.0.0` pending R-003 and DF-003 because implementation and consumer adoption have not started.

## Alternatives rejected by the proposal

- Random observation IDs: not reproducible.
- Traversal index or list position: unstable under ordering changes.
- Raw entity/device/area/label identifiers: unnecessary privacy exposure.
- Display names or localized text: mutable and semantically unstable.
- Unscoped hashing: permits cross-installation correlation and collisions between installations.
- Concatenation without framing: ambiguous byte input.
- Silent scope regeneration: breaks identity without an explicit lifecycle event.
- Collision suffixes: order-dependent and non-deterministic.
- Inferring missing targets: violates authoritative-only semantics.

## Risks retained

| Risk | Treatment | Review significance |
|---|---|---|
| Loss of raw installation scope | Stop new snapshot; preserve last valid stale snapshot | Implementation and operational controls required |
| Clone identity ambiguity | Define logical clone policy; do not auto-detect clones | Operational documentation required |
| Dictionary testing of low-entropy raw IDs | Installation-scoped hash; raw values excluded | Privacy review must accept bounded residual risk |
| Future source API replacement | New governed source capability/version decision | No dynamic remapping |
| Cryptographic collision | Fail affected snapshot; never suffix | Extremely unlikely, behavior nevertheless complete |

## Deterministic vectors

Common raw UUID: `123e4567-e89b-42d3-a456-426614174000`

Public scope: `is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194`

| Category | Canonical key | Observation ID |
|---|---|---|
| API availability | `ck1:api_availability:rest_api_root` | `obs1_90cbe1026ff98c538ec18854829293d38349ca802779bc8d362e948a9481dbcd` |
| Loaded component | `ck1:loaded_component:mqtt` | `obs1_79927229da53e5b9d0b9b2e503f769329d20e7a475285cb24553ee70e903e713` |
| Registered event | `ck1:registered_event_type:state_changed` | `obs1_864d18c0e05d48fc16c99ddd83fc371057b8b8612b0a4010ea6e02baa4046b79` |
| Entity display reference | `ck1:entity_display_reference:ref1_entity_d26423e92d0995348b23e8a0bab951fd9696898a0230020d11896033125b0f92` | `obs1_2916c20e0c01a5b72588d693da87368aafdf654d80ab083eca3a0c26bb40b3c3` |

## R-003 checklist

- [ ] Confirm each canonical key is based only on documented authoritative input.
- [ ] Confirm category/capability mapping is closed and complete for Release 1.
- [ ] Confirm framing and encoding are byte-level deterministic.
- [ ] Confirm installation migration and failure semantics.
- [ ] Confirm reference tokens do not imply object continuity.
- [ ] Confirm relationship target behavior when the target observation is absent.
- [ ] Confirm privacy residual risk is acceptable.
- [ ] Confirm collision, duplicate, and invalid-input behavior.
- [ ] Decide whether amendment before adoption may retain version `1.0.0`.
- [ ] Require DF-003 before resuming I-001B.

## Required DF-003 content if approved

DF-003 must supersede DF-002, enumerate the normative AI-001 documents, state the exact identity and relationship algorithms, record the accepted privacy posture and version decision, preserve the 4/4/4/0/0 scope counts, and explicitly authorize only a subsequent implementation increment to resume.

## Review result represented by this package

AI-001 proposes a complete resolution with no open architectural item inside its authorized scope. This is not approval; the next gate is R-003.

