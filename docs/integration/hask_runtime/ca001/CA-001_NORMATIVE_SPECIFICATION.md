# CA-001 Normative Cryptographic Specification

## Authority boundary

Inherited authority requires deterministic installation-scoped opaque references, secret local material, collision resistance, cross-snapshot stability, no raw identifier/secret disclosure, no cross-installation correlation and fail-closed behavior. CA-001 newly defines the cryptographic bytes below. This proposal does not activate a contract or authorize implementation.

## Format identity

- Cryptographic format name: `hask-opaque-reference-hmac-sha256-v1`.
- Public prefix family: `refh1_`.
- Format version integer: `1`.
- Primitive: HMAC-SHA-256.
- HMAC key: exactly 32 octets.
- HMAC result: all 32 octets; truncation is prohibited.
- Digest text: exactly 64 lowercase hexadecimal ASCII characters.

Any change to the domain, version, field set/order, encoding, framing, key, reference kind or raw identifier is identity-affecting.

## Exact domain-separation bytes

The domain is exactly these 41 ASCII octets, without NUL or newline:

`HASK/HADOCS/OPAQUE-REFERENCE/HMAC-SHA-256`

Hexadecimal:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d323536`

## Integer and text encoding

Every integer is an unsigned 32-bit integer in network byte order (big-endian), exactly four octets. Values outside `0..4294967295` are invalid.

Every text value is first normalized to Unicode NFC, then encoded as strict UTF-8. Ill-formed Unicode, encoding replacement and non-canonical UTF-8 are prohibited.

For text `s`:

```text
TEXT(s) = U32BE(length(UTF8(NFC(s)))) || UTF8(NFC(s))
```

The length is the encoded octet count, not characters. Empty text is invalid for every v1 component. No optional message component exists.

## Canonical input components

Exactly three framed text components occur in this order:

1. `reference_kind`: exactly one of `entity`, `device`, `area`, `label`; lowercase ASCII.
2. `installation_scope`: exact public AI-001-style scope satisfying `is1_[0-9a-f]{64}`; 68 ASCII octets.
3. `raw_identifier`: authoritative sensitive source identifier, non-empty after NFC; control characters U+0000–U+001F and U+007F are invalid; no trimming or case folding.

Hostnames, IP addresses, account IDs, machine identifiers, paths, timestamps and consumer identifiers are prohibited as key material or substitute installation scope.

## Exact HMAC message

Let `D` be the fixed 41 domain octets. The HMAC message is exactly:

```text
D
|| U32BE(1)
|| U32BE(3)
|| TEXT(reference_kind)
|| TEXT(installation_scope)
|| TEXT(raw_identifier)
```

There are no separators, terminators, omitted fields or implementation-defined bytes. The fixed domain length, two fixed-width integers and length-framed components make decoding unambiguous. The component-count integer is always `3`; another value is invalid for v1.

## HMAC and public output

```text
digest = HMAC-SHA-256(key=secret_32_octets, message=message)
public_reference = "refh1_" || reference_kind || "_" || lowercase_hex(digest)
```

Grammar:

```text
public-reference = "refh1_" kind "_" 64lowerhex
kind             = "entity" / "device" / "area" / "label"
64lowerhex       = 64("0"-"9" / "a"-"f")
```

Uppercase hex, padding, truncation, alternate kind spelling and aliases are invalid. The kind in the public prefix must equal the kind authenticated inside the message.

## Reference-kind and installation separation

Reference kind is authenticated as the first framed component, so identical raw text under different kinds has a different message. Installation scope is authenticated as the second component, while the installation-local secret is the HMAC key. Both must match the installation context. Reusing one secret across distinct installations is prohibited.

The public installation scope is not secret and cannot replace the HMAC key. The raw identifier and key are never public output or log fields.

## Validation and fail-closed behavior

Before derivation, validate key length, format version, component count, kind vocabulary, scope grammar, Unicode/NFC conversion, UTF-8 encoding and raw-identifier constraints. On any failure:

- emit no protected reference;
- emit no dependent observation or relationship requiring that reference;
- never fall back to raw ID, unkeyed hashing, another primitive, another key length or another version;
- classify the affected capability using the frozen fail-closed error boundary;
- preserve any last valid immutable snapshot only as explicitly stale.

Equal canonical tuples that produce unequal results indicate implementation failure.

Collision detection is mandatory and installation-wide within one cryptographic
identity context, where that context is the tuple of format version,
installation scope and secret generation. Before a derived reference may be
published, the producer must atomically compare it with a durable private
collision registry covering every canonical tuple previously accepted or
attempted in that context, including tuples from current and retained or deleted
historical snapshots. Snapshot deletion must not remove collision history while
the identity context remains usable.

The registry binds each complete public reference to the exact canonical tuple
used to derive it. It remains internal sensitive state: canonical tuples, raw
identifiers and registry contents are never exported or logged. A missing entry
is registered atomically before publication. An existing entry with the same
canonical tuple is a valid repeat. An existing entry with a different canonical
tuple is a collision.

On collision, registry unavailability, registry corruption or inability to
perform the required atomic comparison, reject the entire affected new
capability snapshot and all dependent observations and relationships. Emit no
new protected reference, never overwrite or repair the registry, never suffix
the reference, and never choose a tuple by traversal or arrival order. A last
valid immutable snapshot may remain only as explicitly stale. Registry state is
separate for a new secret generation or cryptographic format; those transitions
remain subject to the existing snapshot and migration rules.

## Compatibility

AI-001's unkeyed `ref1_` values are not aliases for `refh1_` and are not byte-compatible. A v1 `refh1_` producer must implement this specification exactly. Changes to any normative byte require a new cryptographic format version and prefix; they cannot be introduced as an implementation substitution.

Historical formats may be retained as historical evidence, but one current snapshot uses one reference format only. Contract activation, relationship `source_ref` adoption and contract-version treatment remain outside CA-001.

## Threat boundary

The design protects against an observer who possesses public scope, public references and candidate raw identifiers but not the 256-bit installation secret. It does not protect after secret disclosure, compromised producer execution, malicious source data outside validation limits or unauthorized access to raw identifiers before normalization.
