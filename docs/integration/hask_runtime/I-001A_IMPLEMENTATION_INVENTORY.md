# I-001A Implementation Inventory

Implementation package: `src/hadocs/metadata_collector`

| File | Responsibility |
|---|---|
| `__init__.py` | Stable infrastructure exports and collector identity. |
| `bootstrap.py` | Dependency construction without API clients or runtime wiring. |
| `contract.py` | Frozen contract constants, immutable envelopes and public mapping. |
| `errors.py` | Safe infrastructure error taxonomy. |
| `lifecycle.py` | Configuration, lifecycle, empty snapshot framework and passive scheduler. |
| `normalization.py` | Deterministic ordering, duplicate conflict rejection and contract-name validation. |
| `privacy.py` | PUBLIC/LOCAL preservation and fail-closed SENSITIVE/SECRET treatment. |
| `registry.py` | Five approved categories, four approved predicates and empty capability registry. |
| `serialization.py` | Canonical UTF-8 JSON serialization. |
| `versioning.py` | Contract registration and supported-major negotiation. |

Source files: 10  
Capability implementations: 0  
Home Assistant API clients: 0  
Built-in capabilities: 0  
Runtime/scanner hooks: 0

Implementation source aggregate SHA-256 at validation: `ccb6af7d51fe049c0b7a707c7da3b60998234c42eb3dc3f47ac0a4f027f80744`.

