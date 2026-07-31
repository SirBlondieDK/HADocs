# PI2 Evidence Integration Pipeline Blocker Report

## Decision

PI2 Resume is blocked and is not completed.

The explicit stop condition “HADocs lacks a reliable structured connectivity signal” applies. No production implementation was made.

## Evidence

The normal collector does not obtain config entries, their lifecycle/error state, integration diagnostics, coordinator/update failures, or explicit controller/API connection attempts. Its model provides platform-grouped entities and devices plus raw state/registry data only.

The two authoritative matcher contracts require an explicit failed connectivity result and an explicit problem signal for their respective platform scopes. The available native data cannot establish those facts without vendor-specific or semantic inference.

## Rejected substitutions

- `unavailable` was not treated as a connection failure.
- integration-health `problem` was not treated as a controller/API failure.
- platform identity was not treated as positive evidence.
- generic connectivity entities were not assumed to represent the UniFi controller or MikroTik API.
- test-only observations were not presented as normal-scan support.

These rejections preserve the rules that unknown remains unknown, lifecycle state is not a root cause, and matcher inputs must be based on observations HADocs actually has.

## Impact

- Canonical evidence mapping was not implemented.
- Candidate-only mapping was not implemented.
- Recommendation and verification mapping were not implemented.
- Reports and APIs were not changed.
- Confirmed candidates remain 0.
- Health Score and scoring remain unchanged.
- HASK and Consumer Contract remain unchanged.

## Smallest safe unblock

Define and approve a native, vendor-neutral observation source that carries an explicit integration connection attempt/result and provenance. It should originate from an existing authoritative Home Assistant diagnostic or config-entry signal, not from entity-state inference. Once that input is available, PI2 can resume at the isolated post-native-scan enrichment boundary documented here.

If obtaining this signal requires a new Home Assistant API collector, changed scan scope, or a new input contract, that work needs separate approval before PI2 implementation resumes.

## Verification

The contract-sensitive preflight passed. The complete HADocs suite was rerun in the compatible Python environment: 251 passed. No production source file was changed during the boundary review.

