# AI-002 R-003 Findings Traceability

This register carries all and only the five blocking R-003 findings into AI-002. No closure or correction semantics are asserted in this preflight batch.

| Finding | Severity / class | R-003 finding preserved | Affected AI-001 surface | DF-002 conflict and impact | Required correction / acceptance test | Status |
|---|---|---|---|---|---|---|
| R003-F-001 | CRITICAL / COMPATIBILITY_DEFECT | Public-scope hashing permits dictionary confirmation, while frozen privacy requires non-reversibility without secret local material. | Privacy analysis; source-reference tokens; entity profile; relationship targets | Frozen Privacy Model requires secret local material outside artifacts/logs. Affects entity/device/area/label references, privacy, joins and any dependent canonical key. | Define a fully normative, supported secret-local-material reference mechanism; prove same secret/input is stable, different secret differs, no secret is exported, and failures are fail-closed. | NOT_ADDRESSED |
| R003-F-002 | MAJOR / NORMATIVE_DEFECT | Clone behavior depends on undefined “intended” logical identity with no authoritative declaration or transition. | Installation-scope specification and stability matrix; all categories | Independent implementations could preserve or rotate differently, affecting scope, observation IDs, references and relationships. | Define authoritative classification evidence, safe default, scope/secret rotation, concurrent-clone behavior and deterministic failure; verify every clone/restore/migration case. | NOT_ADDRESSED |
| R003-F-003 | MAJOR / COMPATIBILITY_DEFECT | AI-001 uses entity `obs1_` as `source_ref`; frozen model requires the same opaque token used by the observation (`ref1_entity_`). | Relationship reference rules; entity profile | Changes public relationship endpoint namespace, tuple identity and consumer joins without changing predicates. | Select exactly one frozen-compatible public `source_ref`; specify grammar, inputs, privacy, validation, relationship-ID interaction and migration/version impact. | NOT_ADDRESSED |
| R003-F-004 | MAJOR / NORMATIVE_DEFECT | Removal is `IDENTITY_INVALID` in the matrix but absence-only in profiles/proposal. | Stability matrix; component, event and entity profiles | Ambiguous capability, snapshot, relationship and consumer behavior; historical identity could be invalidated incorrectly. | Define removal, unavailable input, malformed identity and collision separately; prove ordinary removal is unambiguous and historical identity treatment is explicit. | NOT_ADDRESSED |
| R003-F-005 | MAJOR / COMPATIBILITY_DEFECT | Retaining `1.0.0` conflicts with the frozen major-version rule for identity/privacy changes. | Version recommendation; all categories and public reference output | Frozen Version Strategy treats identity/privacy semantic changes as major. | Propose the exact successor major version and document public byte, namespace, migration and coexistence impact without changing the active version. | NOT_ADDRESSED |

## Coverage matrix

| Correction dimension | F-001 | F-002 | F-003 | F-004 | F-005 |
|---|---:|---:|---:|---:|---:|
| Reference privacy | primary | clone copy risk | endpoint token | secret unavailable | version impact |
| Installation stability | secret continuity | primary | same-installation validation | scope unavailable | migration boundary |
| Relationships | target references | regenerate/preserve | primary | removal/dangling | serialized compatibility |
| Categories | entity primary | all four | entity | component/event/entity | all four |
| Versioning | privacy semantics | rotation semantics | endpoint semantics | lifecycle semantics | primary |

Findings represented: **5 of 5**. Additional findings introduced: **0**. Closure decisions are deferred to the authorized correction documents and independent R-004 review.

