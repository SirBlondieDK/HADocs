# A-001 Architecture Defect Resolution — Final Report

## Result

The `websocket_feature` ambiguity is resolved by recommending removal from Collector Contract 1.0.0.

Official Home Assistant documentation classifies `supported_features` as client-originated feature-enablement metadata. It supplies no authoritative server feature value, negotiated protocol-state response or effective runtime-state schema. Retaining the observation would require inference or newly invented semantics.

## Narrow impact

- Release 1 capabilities: 5 → 4
- Release 1 observation categories: 5 → 4
- Relationship predicates: unchanged at 4
- Replacement observations: 0
- Other architecture reviewed: 0

## Governance

A-001 does not modify the frozen specification or implementation. The removal must be incorporated through an updated Architecture Review and new Design Freeze before I-001B resumes.

## Preservation

Production code, runtime, collector implementation, tests, fixtures, HASK, Consumer Contract, PI2 and all unrelated architecture remain unchanged.

## Conclusion

`REMOVE_WEBSOCKET_FEATURE`

