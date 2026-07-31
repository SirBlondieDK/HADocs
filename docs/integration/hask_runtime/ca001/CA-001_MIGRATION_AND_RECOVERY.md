# CA-001 Migration and Recovery

## Identity-affecting changes

Each of the following changes the cryptographic identity context:

- the 32-octet secret;
- any domain byte;
- format-version integer;
- component count, set or ordering;
- integer endianness or width;
- Unicode normalization or UTF-8 rule;
- length framing;
- kind or installation scope;
- raw authoritative identifier;
- HMAC primitive, output length, encoding or public prefix.

No such change may occur silently under `refh1_`.

## Secret loss

Without the exact secret, existing `refh1_` values cannot be reproduced. Loss does not retroactively invalidate historical snapshots. It blocks new protected-reference collection. Automatic key creation is prohibited because it would silently assign new identities under the same apparent installation.

Recovery priority:

1. Restore the exact secret from authorized protected backup.
2. Validate it canonically before collection.
3. Recompute a known synthetic/internal conformance check without logging secret or raw production identifiers.
4. Activate a complete new snapshot only after all dependent references validate.

If exact restoration is impossible, a separately authorized identity reset is required; CA-001 does not authorize it.

## Secret rotation

Rotation is an explicit identity discontinuity. All protected references and every canonical key, observation ID or relationship ID that transitively embeds them must be recomputed. The old and new generations must not be aliased, merged by raw identifier or presented as continuous solely because source data is equal.

Rotation occurs between immutable snapshots. One snapshot cannot contain mixed secret generations. Historical snapshots retain their original reference bytes and provenance. Consumers receive no raw mapping between generations.

## Format migration

A domain, framing, field, version or encoding change requires a new format identifier and a new public prefix, for example a future prefix distinct from `refh1_`. Reusing `refh1_` for changed bytes is prohibited.

Historical and new versions may coexist in storage only as separately versioned immutable snapshots or historical artifacts. They may not coexist as equivalent aliases or mixed references within one current snapshot. Relationships cannot cross cryptographic format generations.

## Backup and host migration

Restoring the exact secret plus the unchanged normative format preserves cryptographic reference bytes when kind, scope and raw identifier also remain equal. Hostname, IP address, filesystem path and machine ID do not participate and therefore do not affect derivation.

An approved migration that intends continuity must transfer the protected secret atomically. A copied environment with the same secret will reproduce the same references; detecting/classifying concurrent clones and deciding separation remain outside CA-001 and require the blocked AI-002 clone architecture.

## Corruption and unavailable storage

Malformed Base64url, incorrect decoded length, unreadable storage or inconsistent concurrent values cause fail-closed behavior. Do not choose one of several values, repair characters, pad non-canonical text, hash the malformed value or regenerate automatically.

The last valid snapshot may remain stale and clearly marked. New observations/relationships requiring protected references are not published until exact recovery or separately authorized reset completes.

## Preventing silent reassignment

- Never alias `ref1_` and `refh1_`.
- Never alias different `refh1_` digests by raw identifier.
- Never reuse a public prefix after normative byte changes.
- Never regenerate a missing secret during ordinary startup.
- Never mix old and new secret generations in one snapshot.
- Preserve format version, secret-generation provenance and snapshot boundary internally without exposing secret material.
- Require an explicit audited authority for rotation/reset.

## Contract boundary

This migration architecture does not activate a contract version, choose relationship `source_ref`, resolve removal semantics or resume AI-002. DF-002 and `hadocs-generic-metadata 1.0.0` remain active.

