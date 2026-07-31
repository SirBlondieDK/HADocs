# Generic Metadata Collector Architecture

Amendment authority: A-001 removes `websocket_feature` and WebSocket `supported_features` from Release 1; no replacement is added.

## Logical components

1. **Capability negotiator** determines which documented capabilities are available without treating absence as failure.
2. **Read-only adapters** call REST or WebSocket operations and return source envelopes without interpretation.
3. **Field gate** rejects everything outside the authoritative allowlist.
4. **Privacy transformer** replaces sensitive identifiers with installation-scoped opaque references and drops forbidden values.
5. **Normalizer** produces canonical observations and explicit relationships.
6. **Snapshot assembler** records capability status, provenance and staleness as an immutable snapshot.
7. **Contract serializer** emits canonical UTF-8 JSON for consumers.

These are responsibilities, not prescribed classes, modules, languages, storage engines or deployment topology.

## Data flow

```text
Documented API -> source envelope -> field gate -> privacy transform
               -> normalization -> immutable snapshot -> public contract
```

There is no path from consumers back to Home Assistant. HASK is a downstream consumer candidate, never a runtime dependency of the collector.

## Source preference

WebSocket is primary when it offers the only documented structured command for an approved capability. REST is primary for API availability, component and event inventories. Equivalent REST/WS data must not be merged unless their documented semantics and snapshot time are equivalent; otherwise each retains separate provenance.

## Architectural guarantees

- No mutating Home Assistant operation.
- No arbitrary endpoint or command invocation.
- No arbitrary field pass-through.
- No inference from missing objects or fields.
- Immutable snapshot after successful assembly.
- Partial success is represented per capability.
- Consumers cannot rely on collection order.
- Output is deterministic for the same normalized inputs and collection metadata.

## Trust boundaries

Home Assistant is the source of explicit facts. The collector is trusted only to preserve allowlisted semantics, privacy transformations and provenance. Consumers must validate contract name/version, snapshot completeness and per-capability status before use. A valid snapshot does not make every observation suitable for diagnosis.

## Deployment independence

The specification does not require an in-process service, daemon, CLI, database or file transport. Scheduling, credentials and storage belong to the future implementation boundary. Credentials never enter the public contract.
