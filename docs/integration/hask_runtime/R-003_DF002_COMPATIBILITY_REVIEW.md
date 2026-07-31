# R-003 DF-002 Compatibility Review

Compatible elements: unchanged 4/4/4 scope; authoritative-only inputs; read-only operation; stable installation-scoped identities; deterministic ordering; no diagnostic semantics.

Compatibility defects:

1. The frozen privacy model requires opaque references to be non-reversible without secret local material and states that secret material remains outside exports. AI-001 derives `ref1_` from a public scope token and guessable raw identifiers without secret local material.
2. The frozen relationship model says references use the same opaque tokens as observations and defines identity over `(predicate, source_ref, target_ref)`. AI-001 changes every relationship source to the entity observation’s `obs1_` ID while its entity’s explicit opaque reference remains `ref1_entity_…`.
3. The frozen version strategy assigns a major version to changed identity rules or privacy treatment. AI-001 recommends retaining `1.0.0` despite adding observable identity semantics and changing the frozen opaque-reference construction.

DF-002 compatibility gate: **FAIL**.
