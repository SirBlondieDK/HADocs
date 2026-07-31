# R-003 Collision Model Review

Canonical-key equality is checked after normalization; identical normalized observations collapse and unequal payloads invalidate the affected capability. Public installation scopes, source references, observation IDs and relationship IDs use full 256-bit SHA-256 digests. A detected digest mapping to unequal canonical tuples invalidates the new snapshot; no overwrite, first/last wins, suffix, timestamp or retry is allowed. Relationships depending on a collided endpoint cannot be published.

The probability of an accidental collision is compatible with the digest size. The rules remain necessary because deterministic failure is part of the contract. Detection can be complete within a produced snapshot by retaining canonical input tuples during normalization; the contract does not claim a global collision oracle.

Collision-model gate: **PASS**.

