# PI2 Rescoping Recommendation

## Required outcome

`PI2_NO_SAFE_EXECUTABLE_SLICE`

No existing matcher simultaneously has fully authoritative executable semantics and a directly compatible signal already collected by normal HADocs scanning.

## Connectivity governance

UniFi and MikroTik remain deferred until a stable contract supplies:

- config-entry reference;
- integration domain;
- explicit test execution or integration-owned status;
- `succeeded`, `failed`, `unknown`, or `not_tested` result;
- distinct disabled, authentication, setup, and connectivity states;
- timestamp or scan context;
- redacted structured metadata.

## Smallest plausible follow-ups

1. Preferred knowledge-first option: migrate one high-value legacy rule to a typed matcher contract only after identifying an already collected native signal with exact semantics. The present analysis found no such pair, so this first requires a separate design increment.
2. Collector option: evaluate a privacy-reviewed structured log-event collector for the five exact log signatures. This is a new native collector increment, not PI2 implementation, and carries significant secret/filtering risk.
3. Upstream option: monitor Home Assistant for a standardized integration-owned connectivity contract.

PI2 must remain blocked. This conclusion does not invalidate Consumer Contract 1.1.0 or the two production matcher contracts.

