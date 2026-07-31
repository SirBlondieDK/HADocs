# A-001 Decision Record

Decision: `REMOVE_WEBSOCKET_FEATURE`

## Context

I-001B demonstrated that the frozen contract does not identify an authoritative server source for `websocket_feature.feature` or `websocket_feature.value`.

## Decision

Remove `websocket_feature` from Collector Contract 1.0.0 and remove WebSocket `supported_features` from the Release 1 metadata capability set. Do not replace it in A-001.

## Evidence basis

The official Home Assistant WebSocket API documents `supported_features` as a client-sent feature-enablement message. It does not document a server capability fact, negotiated value or effective-state response. The Authentication API documents session authorization only.

- <https://developers.home-assistant.io/docs/api/websocket/>
- <https://developers.home-assistant.io/docs/auth_api/>

## Principle alignment

- Authoritative evidence only: restored.
- No inference: restored.
- Read-only: unchanged.
- Deterministic semantics: strengthened by removing an undefined observation.
- Implementation independence: unchanged.
- Version tolerance: unchanged.
- Minimal contract: strengthened.

## Scope

This decision applies only to `websocket_feature`. It reviews no other capability, observation, relationship or release.

