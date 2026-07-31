# Generic Metadata Collector Privacy Model

## Classes and actions

| Class | Default action | Examples |
|---|---|---|
| `PUBLIC` | preserve | protocol feature names and documented enum values |
| `LOCAL` | preserve only if required and non-identifying | component, service and event identifiers |
| `SENSITIVE` | replace with installation-scoped opaque reference or ignore | entity, device, area and label IDs; names; configuration content |
| `SECRET` | never collect or serialize | tokens, cookies, credentials, webhook IDs, certificates, secret URLs |

## Mandatory exclusions

Location, latitude/longitude, IP and MAC addresses, serial numbers, usernames, email addresses, external/internal URLs, filesystem paths, authentication material, arbitrary attributes, raw error messages, configuration bodies, calendar names/content, and event payloads do not enter the public contract.

## Opaque references

Opaque references must be deterministic within an installation privacy scope, non-reversible without secret local material, collision-resistant, and stable enough to join snapshots. The secret material and raw-to-opaque mapping remain outside exported artifacts and logs. Cross-installation correlation is explicitly prohibited.

## Data minimization

Collect the smallest field set required for the declared observation. A documented field is not collected merely because it exists. Source payloads are transient and must not be placed in caches, reports or failure diagnostics after normalization.

## Failure policy

If a value cannot be safely classified or transformed, omit the field. If it is required, mark that capability `partial` or `invalid_response`; never emit the raw value as fallback. Privacy failure is fail-closed for the affected capability, not a reason to stop unrelated collection.

