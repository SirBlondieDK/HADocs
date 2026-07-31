# Generic Metadata Collector Implementation Gate

Design Freeze authorizes no implementation. A separately approved implementation increment must satisfy every gate below before production activation.

## Contract gates

- Conform exactly to `hadocs-generic-metadata` 1.0.0.
- Implement no observation category, field or predicate outside the frozen Release 1 surface.
- Reject unsupported contract major versions and tolerate additive minor elements.
- Produce canonical, repeatable serialization for identical normalized input and metadata.

## Safety and privacy gates

- Use only documented read-only capabilities.
- Complete the opaque-reference security review before enabling entity reference export.
- Prove that credentials, secrets, raw identifiers, payloads and raw errors never enter output or persistent cache.
- Fail closed per capability when classification or transformation fails.

## Compatibility gates

- Build the per-capability Core compatibility matrix, beginning with the discovery baseline 2026.7.3.
- Verify unknown-field ignore, missing-required-field rejection and unsupported-capability behavior.
- Preserve partial, stale, missing, null, empty and false distinctions.

## Operational gates

- Approve bounded retry, timeout, refresh, cache and resource defaults.
- Demonstrate immutable snapshot activation and no invisible stale/current merge.
- Keep the collector disabled until all required gates pass.

## Preservation gates

- No HASK, Consumer Contract, PI2, scoring, UI or recovery semantics may be introduced under this freeze.
- Any architectural change requires a new Architecture Increment; implementation convenience is not sufficient justification.

