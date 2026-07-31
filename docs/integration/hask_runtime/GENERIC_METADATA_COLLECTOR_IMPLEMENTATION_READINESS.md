# Generic Metadata Collector Implementation Readiness

## Decision

The architecture is implementation-ready with minor open items. Release 1 has a bounded capability set, closed observation categories, authoritative field allowlists, privacy transformations, lifecycle, error semantics, compatibility policy and consumer rules. No further API discovery is required to begin a separately approved implementation increment.

## Resolved decisions

- Snapshot rather than subscription architecture.
- Explicit field allowlisting; no generic payload pass-through.
- Only authoritative facts in the public contract.
- Per-capability negotiation and partial failure.
- Stable installation-scoped opaque references for sensitive joins.
- No state/history/event-payload interpretation.
- Separate Release 2 on-demand contract.
- No connectivity claim from current API surface.

## Minor open items

1. No evidence-backed global minimum Core version exists; implementation must build a tested capability matrix.
2. Exact storage, process topology, refresh defaults and retry timings are implementation configuration decisions and cannot change public semantics.
3. The installation-scoped opaque-reference algorithm must undergo security review while preserving the specified guarantees.
4. `entity_display_reference` may be disabled by default if privacy review cannot guarantee stable non-reversible references.

These items do not require architectural redesign or new API discovery. They must be resolved and documented during an explicitly authorized implementation design review before production activation.

## Implementation acceptance gates

No mutating calls; schema and contract conformance; privacy fail-closed behavior; deterministic repeated snapshots; fixture coverage for every status; unknown-field tolerance; unsupported-capability handling; immutable cache; no regressions while disabled; and byte-level proof that HASK, Consumer Contract, PI2 and existing collectors remain unchanged unless separately authorized.

## Conclusion

`READY_WITH_MINOR_OPEN_ITEMS`

