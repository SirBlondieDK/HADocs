# HASK Preview

HASK Preview is an experimental, read-only view of the generated HASK Consumer
Contract bundle. It shows validated bundle status, coverage, relevant platform
knowledge, candidate classifications, supporting evidence categories, missing
evidence, conflicts, and limitations.

> Experimental preview — HASK results are candidate-only and do not affect
> findings, recommendations, Root Causes or Health Score.

## Enable or disable

Both `hask_preview_enabled` and `hask_enabled` must be explicitly `true`.
Everything remains disabled by default. Set `hask_preview_enabled` back to
`false` to disable the page without deleting bundles or operational data.

An explicit `hask_bundle_path` has first priority. If it is missing or corrupt,
HADocs reports that defect and does not silently use another bundle. Without an
explicit path, supported wheel and Windows packages use the validated packaged
bundle. Candidate evaluation additionally retains the independent operational
database, candidate-evidence, and native-status gates.

## Classifications

- `SUPPORTED_CANDIDATE`: bounded evidence supports an experimental candidate.
- `INSUFFICIENT_EVIDENCE`: relevant knowledge exists but required evidence is missing.
- `NO_MATCH`: applicable matchers completed without supporting a problem candidate.
- `NOT_APPLICABLE`: the knowledge does not apply to the observed platform context.
- `REJECTED_CONFLICT`: conflicting evidence rejected the candidate.
- `BUNDLE_DISABLED`, `BUNDLE_UNAVAILABLE`, and `BUNDLE_INVALID`: safe runtime states.

None means confirmed Root Cause. Confirmed Root Causes remain exclusively owned
by normal HADocs analysis.

## Privacy and current limitations

Preview output omits installation scope, raw entity/device/area/config-entry
identifiers, database keys, protected digests, credentials, addresses, URLs, and
raw database rows. The bundle is read-only and separate from the operational
SQLite database. HADocs never writes private installation data into HASK.

Only bounded typed matchers are executable. UniFi and MikroTik remain
`INSUFFICIENT_EVIDENCE` when authoritative controller/API results are absent.
Tuya uses only Home Assistant's collected native config-entry lifecycle aggregate;
a reported problem does not identify a physical-device, cloud, account, network,
or code root cause. HADocs performs no authenticated probe, controller login, or
fabricated connectivity inference.

Matcher applicability is currently derived from persisted entity/platform
relationships. A Tuya config entry that exposes no entities can therefore appear
as `NOT_APPLICABLE` even when native status observed the config entry. That state
does not establish that Tuya is absent or not installed; it means there is no
persisted subject to which the current candidate matcher can attach.
