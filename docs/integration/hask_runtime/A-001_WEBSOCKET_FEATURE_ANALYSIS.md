# A-001 WebSocket Feature Analysis

## Authoritative origin

Classification: `CLIENT_DECLARATION`

The official WebSocket documentation states that clients supporting features that need enabling send `supported_features` as their first message after authentication. Its example places `coalesce_messages: 1` inside the client-supplied `features` object. It further describes the effect—messages are sent coalesced rather than individually—but does not define a returned feature catalog or effective-state payload.

Official source: <https://developers.home-assistant.io/docs/api/websocket/>

## Semantic classification

| Candidate meaning | Supported by official documentation? | Result |
|---|---:|---|
| Home Assistant fact | No | The value originates in the client message. |
| Client metadata/declaration | Yes | This is the documented origin. |
| Protocol feature enablement request | Yes | The message enables client-supported behavior. |
| Negotiated protocol state | No | No negotiation result schema is documented. |
| Documented server state | No | No server state field is documented. |
| Effective runtime capability | No | No authoritative effective-value response is documented. |
| Derived information | Only by inference | A successful connection or later batching cannot be converted into the frozen observation. |

## Authentication boundary

The official Authentication API says an access token is supplied in the WebSocket authentication message. Successful authentication permits the command phase. It does not attest to the meaning, acceptance or effective state of `supported_features` values.

Official source: <https://developers.home-assistant.io/docs/auth_api/>

## Contract fitness

- Complete semantics: FAIL
- Deterministic authoritative semantics: FAIL
- Stable Home Assistant fact: FAIL
- Inference-free normalization: FAIL
- Versionable as a server observation: FAIL
- Suitable as HASK authoritative evidence: FAIL

The message could be represented in a different product as client configuration or transport behavior, but that would be a new semantic design outside A-001. It cannot remain as the frozen authoritative metadata observation.

