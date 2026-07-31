# AI-001 Options Analysis

## Canonical key

| Option | Strengths | Defects | Decision |
|---|---|---|---|
| Canonical JSON | Structured and extensible | Verbose public identity; more escaping and number rules than Release 1 needs | Rejected |
| Category-specific tuple with unspecified serializer | Compact conceptual model | Leaves byte choices unresolved | Rejected |
| Versioned normalized text grammar | Deterministic, inspectable, easy to validate | Requires strict escaping rules | Preferred |

## Installation scope

| Option | Stability/privacy | Portability/restore | Decision |
|---|---|---|---|
| Home Assistant identifier | No approved authoritative API field in DF-002 | Unknown | Rejected |
| Derive from URL/hostname/address | Leaks mutable local topology | Poor | Rejected |
| Collector-managed persistent UUIDv4, publicly hashed | Stable, private, independent of HA metadata | Explicit backup/migration rules required | Preferred |

## Observation ID

| Option | Determinism/privacy | Collision/debugging | Decision |
|---|---|---|---|
| Direct structured tuple | Exposes scope/key components | No digest collision | Rejected for privacy |
| Prefixed canonical text | Debuggable but exposes sensitive components | No digest collision | Rejected |
| Domain-separated SHA-256 over length-framed inputs | Deterministic and non-revealing | Cryptographic collision policy required | Preferred |

## Source capability

| Option | Stability | Decision |
|---|---|---|
| Adapter/class identifiers | Implementation-coupled | Rejected |
| Raw endpoint/command strings | Stable today but inconsistent grammar | Rejected |
| Closed public vocabulary derived once from frozen capabilities | Stable and versionable | Preferred |

The preferred combination optimizes normative clarity, privacy and consumer interoperability rather than implementation convenience.

