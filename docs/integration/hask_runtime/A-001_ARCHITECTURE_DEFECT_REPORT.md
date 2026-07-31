# A-001 Architecture Defect Report

Subject: `websocket_feature` Contract Ambiguity  
Date: 2026-07-24  
Baseline: DF-001, Collector Contract 1.0.0

## Defect

The frozen observation model classifies `websocket_feature` as an authoritative Home Assistant observation sourced from WebSocket `supported_features`. Official Home Assistant documentation instead defines `supported_features` as a message sent by a client that supports features requiring enablement. The documented `features.coalesce_messages` value is supplied by the client.

The documentation does not define a server capability inventory, a server-returned feature value, or a negotiated/effective feature-state object for this message. Consequently, the frozen observation's required `feature` and `value` cannot be populated as Home Assistant facts without inference.

## Evidence

- Home Assistant WebSocket API, “Feature enablement phase”: <https://developers.home-assistant.io/docs/api/websocket/>
- Home Assistant Authentication API, authenticated WebSocket access: <https://developers.home-assistant.io/docs/auth_api/>
- Frozen `GENERIC_METADATA_COLLECTOR_OBSERVATION_MODEL.md`
- I-001B `IMPLEMENTATION_SCOPE_BLOCKER.md`

The authentication documentation establishes how a client authenticates to use the API. It does not promote client-submitted feature metadata into server facts.

## Defect classification

Contract semantic defect, isolated to `websocket_feature`. No other observation or Release 1 capability was reviewed.

## Resolution recommendation

Remove `websocket_feature` and its `supported_features` collection capability from Collector Contract 1.0.0 before Release 1 implementation resumes.

