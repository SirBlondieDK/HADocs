# AI-002 Frozen AI-001 Inventory

The following AI-001 rules are outside AI-002’s correction authority and remain unchanged. AI-002 documents must reference rather than reproduce or silently amend them.

| Frozen rule | AI-001 evidence | Reason outside scope | Byte impact | Semantic impact |
|---|---|---|---|---|
| Canonical-key grammar `ck1:<category>:<component>` | Canonical Key Specification | R-003 key gate passed | NONE | NONE |
| NFC normalization and UTF-8 percent encoding | Canonical Key Specification | Not challenged by any finding | NONE | NONE |
| Four category-specific key profiles | Category Identity Profiles | Category names/inputs frozen except direct corrected-reference dependency | NONE* | NONE* |
| Closed source-capability vocabulary and grammar | Source Capability Specification | R-003 source-capability gate passed | NONE | NONE |
| Observation-ID field order | Observation ID Specification | R-003 observation-ID gate passed | NONE | NONE |
| Four-byte big-endian length framing and NFC UTF-8 bytes | Observation ID Specification | Independently reproduced by R-003 | NONE | NONE |
| Observation-ID domain separator and SHA-256 | Observation ID Specification | Not challenged | NONE | NONE |
| `obs1_[0-9a-f]{64}` grammar | Observation ID Specification | Not challenged | NONE | NONE |
| Observation-ID collision rejection | Observation ID Specification / proposal | R-003 collision gate passed | NONE | NONE |
| Deterministic lexicographic ordering | Architecture Proposal | Not challenged | NONE | NONE |
| Capability count and names | DF-002 / AI-001 scope | Scope change prohibited | NONE | NONE |
| Observation-category count and names | DF-002 / AI-001 profiles | Scope change prohibited | NONE | NONE |
| Relationship-predicate count and names | DF-002 / relationship rules | Predicate change prohibited | NONE | NONE |
| Release 1 scope | DF-002 / AI-001 proposal | Expansion or reduction prohibited | NONE | NONE |
| Default-disabled behavior | AI-001 frozen-area declaration | Not implicated by findings | NONE | NONE |
| `websocket_feature` remains removed | DF-002 amendment history | Restoration prohibited | NONE | NONE |
| WebSocket `supported_features` remains removed | DF-002 amendment history | Restoration prohibited | NONE | NONE |

`*` F-001 may change the private derivation and therefore the resulting `ref1_` component used by `entity_display_reference`; F-003 may change relationship endpoint use. These are recorded dependencies, not permission to change canonical-key grammar, category mapping or observation-ID algorithm. Resulting downstream bytes must be inventoried explicitly in later correction documents.

## Preservation assertions

- AI-001 artifacts remain immutable historical proposal evidence.
- R-003 artifacts remain immutable review evidence.
- DF-002 remains the active implementation baseline.
- Active contract version remains `hadocs-generic-metadata 1.0.0`.
- AI-002 introduces no correction outside R003-F-001 through R003-F-005.

Frozen inventory status: **COMPLETE FOR PREFLIGHT**. It does not decide any correction semantics.
