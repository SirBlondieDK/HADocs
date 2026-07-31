# AI-001 Identity Requirements

## MUST

- Produce installation-scoped unique, cross-snapshot-stable identities from authoritative category inputs.
- Define identical canonical text, UTF-8 bytes, component order and digest output for independent producers.
- Preserve source case after NFC normalization; never use display labels or traversal order.
- Keep sensitive raw IDs and the raw installation identifier out of public output and logs.
- Use one closed source-capability value per Release 1 capability.
- Make relationship references deterministic and validate their installation scope.
- Reject missing identity inputs, conflicting duplicates and detected digest collisions.
- Preserve identities across restart, backup restore and explicit migration when the same scope and source identity persist.
- Change identities when installation scope, category or canonical identity input changes.

## MUST NOT

- Use timestamps, random per-snapshot values, memory/process IDs, paths, URLs, addresses, credentials, friendly names, translations or consumer IDs.
- Trim, case-fold, guess, alias or synthesize missing authoritative source identifiers.
- Repair collisions by suffixing or ordering-dependent retries.
- rotate installation scope automatically.

## SHOULD

- Use domain-separated SHA-256 and explicit length framing.
- Keep public tokens recognizable by fixed versioned prefixes.
- Preserve the last valid immutable snapshot when persistent scope becomes unreadable.

## MAY

- Store the raw installation scope in implementation-selected local persistent storage that satisfies the normative persistence and access requirements.
- expose public scope, source reference, observation and relationship tokens in operational logs because raw inputs cannot be recovered from them.

Absent required identity input produces no affected observation. Invalid global installation scope prevents activation of a new snapshot. Unsupported capabilities produce the frozen `unsupported` status and no observation.

