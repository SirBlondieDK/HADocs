# AI-002 Authorized Scope

## Authority

AI-002 is a narrow documentation and architecture-correction increment governed by G-001 and resumed under G-002. DF-002 remains authoritative for implementation. AI-001 is the unapproved base proposal; R-003 is the sole correction authority.

## Authorized corrections

AI-002 may address only:

1. **C-001 / R003-F-001:** secret local material and reference-hash compatibility.
2. **C-002 / R003-F-002:** clone identity, authoritative classification and rotation.
3. **C-003 / R003-F-003:** relationship `source_ref` representation.
4. **C-004 / R003-F-004:** removal semantics versus `IDENTITY_INVALID`.
5. **C-005 / R003-F-005:** major-version compatibility.

R-003’s findings register, review decision, DF-003 readiness report, final report and final state define the correction boundary. Missing or non-unique authority for any correction triggers a blocker; AI-002 must not guess.

## Frozen AI-001 surface

Except for a direct dependency of one of the five findings, AI-002 must preserve canonical-key architecture, source-capability vocabulary, observation-ID construction, collision model, deterministic ordering, the four capabilities, four categories, four predicates, Release 1 scope, default-disabled behavior and the removal of `websocket_feature` and WebSocket `supported_features`.

AI-001 and R-003 files must not be edited. Corrections, if supportable, must be separate AI-002 amendment documents with explicit precedence.

## Prohibited work

AI-002 does not authorize production code, tests, fixtures, implementation configuration, dependencies, contract activation, DF-003, R-004 execution, I-001B_RESUME_2, V-001, HASK, Consumer Contract, PI2, consumer adoption, scope changes or unrelated cleanup.

## Success and blocker criteria

Success requires all five findings to be `CLOSED` or `CLOSED_WITH_NOTES`, deterministic normative vectors where bytes change, no changes outside the five findings, and a complete R-004 review package. AI-002 cannot self-approve.

AI-002 must stop if authority is missing or contradictory, a correction requires an unrelated redesign, a cryptographic choice cannot be uniquely supported, or an out-of-scope defect blocks the correction.

## Governance sequence

`AI-001 → R-003 → AI-002 → R-004 → DF-003 → I-001B_RESUME_2 → V-001`

Only AI-002 is active. R-004 is the next possible authority after successful completion; implementation remains prohibited until an approved R-004 and completed DF-003.

