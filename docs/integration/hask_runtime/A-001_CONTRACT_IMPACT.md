# A-001 Contract Impact

## Required narrow change

Remove only:

- Release 1 capability: WebSocket `supported_features`
- Observation category: `websocket_feature`
- Its required fields: `feature`, `value`

No substitute observation is introduced.

## Impact matrix

| Surface | Impact |
|---|---|
| Release 1 | Reduces approved capabilities from five to four and observation categories from five to four. |
| Collector Contract 1.0.0 | Removes one not-yet-implemented observation category from the frozen baseline. A superseding review/freeze is required before implementation. |
| Observation Model | Removes the `websocket_feature` row only. |
| Relationship Model | No impact; `websocket_feature` defines no relationship. Four predicates remain unchanged. |
| Privacy Model | No impact; removal exports less data. |
| Lifecycle and version strategy | No impact. |
| Release Plan | Release 1 no longer lists WebSocket feature negotiation as collectable metadata. |
| Future collectors | `supported_features` remains available for transport configuration where appropriate, but not as an authoritative metadata observation under this contract. |
| HASK evidence | Removes a semantically unsafe candidate; no authoritative evidence is lost because none was established. |

## Architectural effect

Removal simplifies Release 1 by eliminating a client-originated transport declaration from a server-fact collector. It strengthens the existing principles of authoritative evidence, minimal scope and no inference. It does not expand or redesign Release 1.

## Governance consequence

DF-001 remains the current recorded freeze until the defect resolution is incorporated through the required Architecture Review and new Design Freeze. I-001B must remain blocked until that governance path completes.

