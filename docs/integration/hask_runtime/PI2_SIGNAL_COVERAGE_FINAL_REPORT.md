# PI2 Signal Coverage Final Report

## Executive conclusion

`PI2_NO_SAFE_EXECUTABLE_SLICE`

The analysis completed all 25 matcher assessments without changing production code, tests, fixtures, HASK, schemas, matcher contracts, or Consumer Contract content.

## Findings

- HADocs normal scanning has strong structured inventory and state coverage but no integration connection-test observation, Home Assistant log stream, config-entry collection, backup inventory, or verification-result collection.
- UniFi and MikroTik typed matcher contracts are complete, deterministic, candidate-only, and reference-consumer validated. Their required native signal is absent.
- Five legacy log patterns have precise signatures, but their source is not collected and raw-log ingestion presents privacy risk.
- Eighteen legacy rules do not export sufficient closed execution semantics. Related native data cannot repair that contract gap without local interpretation.
- No matcher qualifies for `DIRECT_EXPLICIT_MATCH` or `SAFE_NORMALIZATION_REQUIRED`.

## Preservation and quality

- HADocs: 251 passed
- HASK: 88 passed
- HASK validators: all PASS
- Confirmed candidates: 0
- Health Score changes: 0
- Production/test/fixture changes: 0
- HASK and Consumer Contract changes: 0
- Deterministic report generation: two identical passes; aggregate SHA-256 recorded in the final state

## Governance

Connectivity remains deferred. PI2 remains blocked. Completion of this analysis does not authorize implementation or PI3.
