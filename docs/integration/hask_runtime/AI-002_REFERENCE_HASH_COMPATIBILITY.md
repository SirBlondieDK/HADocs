# AI-002 Reference-Hash Compatibility

## Gate purpose

This document evaluates only R003-F-001: whether existing authority uniquely determines a DF-002-compatible reference-hash construction. It does not select or recommend a cryptographic primitive.

## Authoritative requirements reconstructed

The frozen Privacy Model requires opaque references to be:

- deterministic within an installation privacy scope;
- non-reversible without secret local material;
- collision-resistant;
- stable enough to join snapshots;
- based on secret material and raw-to-opaque data that remain outside exported artifacts and logs;
- non-correlatable across installations.

The frozen failure policy requires unsafe optional values to be omitted and unsafe required values to fail closed for the affected capability. DF-002 remains the active baseline. AI-001 proposed an unkeyed digest over public installation scope and raw identifier. R-003 established that this permits dictionary confirmation and is incompatible with the frozen secret-local-material requirement.

The active Collector Contract additionally requires stable installation-scoped opaque references and prohibits recovery of sensitive source identifiers from public observation identity. It does not define the private cryptographic construction.

## Determinations supported by authority

Existing authority uniquely requires that:

1. A private secret input participate in reference derivation.
2. The public installation-scope token alone is insufficient as that private input.
3. Raw source identifiers and secret material are not serialized or logged.
4. Equal authoritative source input under the same preserved installation privacy context produces the same public reference.
5. Cross-installation public references must not be correlatable by using a shared public derivation context.
6. Missing, corrupt or unusable secret material must fail closed for the affected capability; raw identifiers are never a fallback.
7. Collision handling must be deterministic and must not silently overwrite, suffix or select by traversal order.

## Missing normative authority

The reviewed authority does **not** uniquely specify:

- the keyed cryptographic primitive;
- its exact domain-separation bytes;
- secret length or minimum entropy;
- secret encoding;
- exact input framing and field order for the keyed operation;
- whether and how the existing `ref1_` format-version namespace changes;
- exact key-generation and validation rules;
- normative cryptographic test vectors.

Several constructions could satisfy the high-level frozen properties while producing different public bytes. Choosing one would create public identity semantics not uniquely derived from DF-002, AI-001, R-003 or the active contract. AI-002’s ambiguity rule prohibits that choice.

## Compatibility result

The incompatibility identified by R003-F-001 is confirmed, but it cannot be corrected under the available authority without an additional architecture decision.

Reference-hash compatibility: **BLOCKED**.

No correction rule, public reference bytes, prefix change, migration rule or test vector is approved by this document.

