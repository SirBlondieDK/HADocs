# API Field Stability Report

Home Assistant's documented Core APIs do not expose a general schema version or field-level compatibility guarantee. Stability classifications therefore describe evidence, not promises:

- `DOCUMENTED_CURRENT_UNVERSIONED`: current official documentation, guarantee unspecified.
- `DOCUMENTED_COMMAND_SCHEMA_NOT_DOCUMENTED`: command appears in an official example, but its wire schema is not specified.
- `DOCUMENTED_CURRENT_COMPACT_OPTIONAL_FIELDS`: display registry uses compact keys and conditional omission.
- `OBSERVED_UNDOCUMENTED`: present on Core 2026.7.3 only; never authoritative alone.

Known explicit migration signals include the 2025 removal of action translations from service responses and deprecation of token revocation through `/auth/token` in favor of `/auth/revoke`.

Consumers should validate envelopes, tolerate documented optional fields, allowlist fields, record Core version, and fail closed when semantic identity changes.

