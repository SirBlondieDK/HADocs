# I-001B Implementation Scope Blocker

Date: 2026-07-24  
Program: I-001B Generic Metadata Collector Release 1 Capability Implementation  
Governance baseline: DF-001  
Contract: `hadocs-generic-metadata` 1.0.0

## Decision

`IMPLEMENTATION_BLOCKED`

I-001B stopped during Step 1 before any implementation change. The approved Release 1 scope is enumerable, but one mandatory observation cannot be implemented without selecting public semantics that the frozen contract does not define.

## Approved Release 1 inventory

| Capability | Interface | Observation | Relationships | Privacy |
|---|---|---|---|---|
| `GET /api/` | REST | `api_availability` | none | LOCAL response; message excluded |
| `GET /api/components` | REST | `loaded_component` | none | LOCAL identifiers preserved |
| `GET /api/events` | REST | `registered_event_type` | none | event type preserved; listener count excluded |
| `supported_features` | WebSocket | `websocket_feature` | none | PUBLIC feature/value |
| `config/entity_registry/list_for_display` | WebSocket, optional | `entity_display_reference` | four frozen entity predicates | raw identifiers require installation-scoped opaque transformation |

The scope itself contains five capabilities, five observation categories and four relationship predicates. No Release 2 or Release 3 capability is needed to enumerate it.

## Blocking ambiguity

The frozen observation model requires `websocket_feature` with authoritative fields `feature` and `value`, sourced from WebSocket `supported_features`. The frozen atlas/specification describes the command as feature negotiation and lists `features.coalesce_messages:integer`, but the producer contract does not state which of these is the authoritative observation source:

1. the feature/value submitted by the collector in the command request;
2. a feature/value returned by Home Assistant in the command result; or
3. a separately established negotiated/effective feature value.

Choosing option 1 would risk exporting a client declaration as a Home Assistant fact. Choosing options 2 or 3 requires response/effective semantics not specified by the frozen contract. Echoing a requested value, interpreting success as acceptance, or inventing a negotiated value would violate the frozen prohibitions on inference and additional semantics.

This is an architectural/contract ambiguity because the choice changes the meaning and authority of a public Release 1 observation. It cannot be resolved by transport injection, normalization, validation or an implementation default.

## Secondary gated item

The optional `entity_display_reference` adapter can be structured, but it cannot be enabled until the already recorded opaque-reference security review is complete. This is an implementation gate rather than the present architecture blocker; no algorithm was selected or implemented by I-001B.

## Required governance path

DF-001 change control requires:

1. Demonstrate the architecture defect.
2. Approve a narrowly scoped Architecture Increment defining or removing the `websocket_feature` semantics.
3. Perform a new Architecture Review.
4. Establish a new Design Freeze.
5. Resume I-001B against the superseding frozen baseline.

Implementation convenience is not sufficient. No new API discovery, contract reinterpretation or undocumented API use was performed.

## Preservation validation

- I-001B production/source changes: 0
- Release 1 capability implementations added: 0
- I-001A infrastructure modified: 0
- DF-001 modified: 0
- Frozen specification modified: 0
- HASK modified: 0
- Consumer Contract modified: 0
- PI2 modified: 0
- Tests or fixtures modified: 0

