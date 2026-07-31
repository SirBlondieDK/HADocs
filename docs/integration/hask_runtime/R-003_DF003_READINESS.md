# R-003 DF-003 Readiness

DF-003 cannot be a pure Design Freeze today. It would have to choose:

- secret/local material and reconstruction semantics for opaque references;
- authoritative clone classification and rotation;
- `obs1_` versus `ref1_entity_` relationship source endpoints;
- absence versus invalid identity on source removal.

Those are architecture decisions, prohibited in a freeze. DF-003 would also need a version outcome founded on a corrected architecture.

DF-003 readiness: **NOT_READY_FOR_DF003**.

Required sequence: AI-002 narrow correction → independent review → DF-003. DF-002 remains active and implementation remains blocked.

