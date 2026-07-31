# AI-002 Secret Local Material Specification

## Status

This document records the maximum secret-local-material specification supported by existing authority. Undetermined fields remain explicitly blocked; they are not filled with implementation convention.

## Normative properties established by existing authority

| Property | Authority-supported requirement |
|---|---|
| Purpose | Prevent public reference derivation from being reproducible without private installation-local material. |
| Conceptual classification | `SECRET`; never public contract data. |
| Persistence | Must remain available for stable references across ordinary snapshots and lifecycle events where the same installation privacy context is preserved. |
| Access | Restricted to the future producer function that derives opaque references. |
| Serialization | Prohibited in observations, relationships, snapshots, reports, diagnostics and consumer output. |
| Logging | Prohibited. |
| Network dependency | None is authorized. |
| Public installation scope | Distinct from the secret and insufficient as a substitute. |
| Raw identifiers | Remain private inputs and may not be emitted as fallback. |
| Failure posture | Missing, corrupt or unusable secret material fails closed for the affected capability. |
| Cross-installation behavior | Must prevent intentional public cross-installation correlation. |
| Determinism | Same protected context and same canonical raw identifier must reproduce the same opaque reference. |

## Fields not determined by authority

Existing authority does not uniquely determine:

- normative secret name in the public architecture;
- exact secret data type and encoding;
- minimum bit entropy or length;
- generation algorithm;
- creation timing and generation authority;
- storage abstraction beyond being local, private and outside public artifacts/logs;
- backup inclusion details;
- restore and migration transfer mechanics;
- clone copy/rotation mechanics;
- authorized manual rotation mechanism;
- corruption-detection representation;
- recovery after secret loss;
- exact relationship between secret rotation, `installation_scope`, `canonical_key`, `observation_id`, `source_ref` and relationships;
- synthetic vector secret length and byte format.

Those choices affect stable public references and downstream observation or relationship bytes. They cannot be classified as mere implementation defaults.

## Lifecycle boundary

Authority supports only these non-controversial outcomes:

- Ordinary repeated collection requires the same private context to preserve reference stability.
- Secret unavailability requires fail-closed collection for affected references.
- Secret disclosure in output or logs is prohibited.

Restart, update, backup, restore, migration, clone, reinstall, loss, corruption and authorized rotation cannot receive complete `MUST_REMAIN`, `MUST_ROTATE`, `MAY_ROTATE` or `MUST_FAIL` outcomes until the missing creation, portability and rotation authority is supplied. AI-002 may not infer those outcomes here.

## Specification result

Secret-local-material requirements are partially reconstructable, but a complete normative specification is **BLOCKED** by missing cryptographic and lifecycle authority.

No real or synthetic secret, cryptographic construction or public reference vector is introduced.

