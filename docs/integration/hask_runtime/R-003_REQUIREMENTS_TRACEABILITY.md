# R-003 Requirements Traceability

| Blocker requirement | AI-001 decision/specification | Profile/stability/privacy/relationship/vector | Review result |
|---|---|---|---|
| Canonical key per category | `ck1:<category>:<component>`; category-specific component | four profiles; stability matrix; four vectors | traced; key gate PASS |
| Normative observation-ID encoding | framed NFC UTF-8 tuple, SHA-256, `obs1_` | observation-ID spec; four vectors | traced; ID gate PASS |
| Installation scope source/representation | persistent UUIDv4; public `is1_` digest | scope spec; stability/privacy | traced; privacy conflict FAIL |
| Canonical source capability | closed four-value map | source capability spec; profiles | traced; PASS |
| Installation-scoped stability | public scope participates in references and IDs | scope spec; stability matrix | traced; clone rule incomplete |
| Cross-snapshot stability | persistent scope plus canonical inputs | profiles; matrix | traced; removal terminology conflicts |
| Relationship references | entity observation ID / typed target tokens | relationship rules | traced; DF-002 endpoint conflict |
| Collision behavior | fail affected snapshot, no suffix | key/ID/relationship specs | traced; PASS |
| Versioning treatment | retain 1.0.0 pending review/freeze | version recommendation | traced; frozen strategy requires major |

All initiating items have an AI-001 location and review criterion. Traceability gate: **PASS**. Traceability does not cure the listed defects.

