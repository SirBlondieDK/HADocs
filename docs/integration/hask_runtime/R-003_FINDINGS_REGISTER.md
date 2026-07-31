# R-003 Findings Register

| ID | Severity / class | Artifact / concept / category | Finding and evidence | Impact and disposition |
|---|---|---|---|---|
| R003-F-001 | CRITICAL / COMPATIBILITY_DEFECT | Privacy analysis; reference tokens; entity | Public-scope hashing permits dictionary confirmation, while frozen privacy requires non-reversibility without secret local material | Privacy and compatibility; DF-003 cannot design. New narrow privacy/identity architecture correction required. |
| R003-F-002 | MAJOR / NORMATIVE_DEFECT | Installation scope; all categories | Clone behavior depends on undefined “intended” logical identity with no authoritative declaration or transition | Determinism/portability; implementation choice required. Correction must define clone classification/rotation semantics. |
| R003-F-003 | MAJOR / COMPATIBILITY_DEFECT | Relationship rules; entity | AI-001 uses entity `obs1_` as `source_ref`; frozen model requires the same opaque reference token used by the observation (`ref1_entity_`) | Changes public relationship tuple and joins. Correction must reconcile endpoint semantics without new predicates. |
| R003-F-004 | MAJOR / NORMATIVE_DEFECT | Stability matrix; component/event/entity | Removal is `IDENTITY_INVALID` in matrix but absence-only in profiles/proposal | Capability/lifecycle behavior ambiguous. Correction must select one existing semantic outcome. |
| R003-F-005 | MAJOR / COMPATIBILITY_DEFECT | Version recommendation; all | Retaining 1.0.0 conflicts with frozen major-version rule for identity/privacy changes | Compatibility/governance. Corrected review must recommend major; freeze records outcome. |

All findings affect implementation choices; none can be omitted. DF-003 could record none of F-001 through F-004 without designing. F-005 is determinable by review but cannot be applied until the architectural defects are corrected.

Counts: INFO 0, MINOR 0, MAJOR 4, CRITICAL 1. EDITORIAL 0, CLARIFICATION_ONLY 0, NORMATIVE_DEFECT 2, COMPATIBILITY_DEFECT 3, EVIDENCE_DEFECT 0.

Smallest follow-up: one narrowly bounded **AI-002 Observation Identity Compatibility Correction** addressing only reference privacy material, clone lifecycle authority, relationship endpoint token, removal semantics and consequent version recommendation; then a new independent review.

