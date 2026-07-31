# AI-002 Blocker Report

## Blocked increment

`AI-002 – Observation Identity Compatibility Correction`

## Trigger

The cryptographic authority gate for R003-F-001 failed. DF-002 specifies required security properties and secret-local-material participation but does not uniquely determine the keyed construction, secret format, entropy, input bytes or lifecycle semantics needed to produce stable public references.

AI-002 explicitly requires a stop when a cryptographic construction would require an arbitrary architecture choice. Selecting a common construction would violate G-001’s prohibition on implementation-defined contract semantics and AI-002’s ambiguity rule.

## Unresolved finding

- Finding: `R003-F-001`
- Severity: CRITICAL
- Classification: COMPATIBILITY_DEFECT
- Closure status: `BLOCKED`
- Affected concept: opaque entity/device/area/label reference derivation
- Downstream blocked areas: secret lifecycle, clone identity, relationship `source_ref`, stability matrix, privacy amendment, category impact, consolidated amendment and version proposal

R003-F-002 through R003-F-005 were not corrected. Continuing to them would violate the approved batch boundary and could make their conclusions depend on an undefined reference mechanism.

## Preserved state

- G-001 and G-002 remain permanent governance.
- DF-002 remains the active implementation baseline.
- Active contract remains `hadocs-generic-metadata 1.0.0`.
- AI-001 remains an unapproved immutable proposal.
- R-003 remains immutable review evidence.
- Production implementation remains prohibited.
- No contract, production source, test, fixture, dependency, configuration or frozen governance file was changed.

## Smallest unblock increment

A separately authorized, narrow cryptographic architecture decision must define the private reference derivation completely, including primitive, domain separation, input framing, secret requirements, lifecycle/rotation consequences, output-version treatment and deterministic synthetic vectors. It must be independently reviewed before AI-002 can be resumed or superseded.

AI-002 conclusion: `OBSERVATION_IDENTITY_COMPATIBILITY_BLOCKED`.

