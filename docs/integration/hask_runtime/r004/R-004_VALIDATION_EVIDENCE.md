# R-004 Validation Evidence

## Governance gate

- Sole active authority: `R-004`.
- CA-001: `COMPLETE`, preserved read-only.
- AI-002: `BLOCKED`.
- Active implementation baseline: `DF-002`.
- Implementation and contract changes: not authorized.
- Initial R-004 output inventory: directory absent; all three requested deliverables `MISSING`.

## Reviewed documents

All ten required CA-001 documents were read in full:

1. `CA-001_EXISTING_AUTHORITY.md`
2. `CA-001_REQUIREMENTS.md`
3. `CA-001_OPEN_DECISIONS.md`
4. `CA-001_DECISION_CRITERIA.md`
5. `CA-001_ARCHITECTURE_ALTERNATIVES.md`
6. `CA-001_RECOMMENDED_ARCHITECTURE.md`
7. `CA-001_NORMATIVE_SPECIFICATION.md`
8. `CA-001_SECRET_LIFECYCLE.md`
9. `CA-001_MIGRATION_AND_RECOVERY.md`
10. `CA-001_TEST_VECTORS.md`

The comparison baseline included DF-002, AI-001, R-003 and the active governance summaries. In particular, the review traced the frozen secret-local-material requirement to the frozen Privacy Model and R003-F-001, while treating R003-F-002 through R003-F-005 as deliberately outside CA-001's narrow correction authority.

## Byte-level specification checks

The reviewer independently reconstructed the message as:

```text
ASCII("HASK/HADOCS/OPAQUE-REFERENCE/HMAC-SHA-256")
|| U32BE(1)
|| U32BE(3)
|| U32BE(len(UTF8(NFC(kind)))) || UTF8(NFC(kind))
|| U32BE(len(UTF8(NFC(scope)))) || UTF8(NFC(scope))
|| U32BE(len(UTF8(NFC(raw_identifier)))) || UTF8(NFC(raw_identifier))
```

Checks:

- domain: exactly 41 ASCII octets;
- version and component count: unsigned 32-bit big-endian;
- component order: kind, scope, raw identifier;
- text: NFC followed by strict UTF-8;
- lengths: encoded-octet counts;
- key: exactly 32 octets;
- output: complete 32-octet HMAC-SHA-256 result;
- public digest: exactly 64 lowercase hexadecimal characters;
- truncation: prohibited;
- kind: authenticated in the message and repeated consistently in the public prefix.

No ambiguous concatenation or implementation-selected byte appears in the v1 derivation.

## Independent test-vector recomputation

Two independent runtime implementations reconstructed inputs from the normative prose rather than hashing copied message bytes:

- Python standard-library `hmac`/`hashlib`;
- .NET `HMACSHA256` with independently implemented NFC, UTF-8 and U32BE framing.

| Vector | Python | .NET | Expected digest |
|---|---|---|---|
| V1 entity ASCII | PASS | PASS | `312675c4bb1c9ddc1caffc38c97bf0bc686bfb45909d60cd0d629355a296352d` |
| V2 device Unicode | PASS | PASS | `c4bb39925ca26b54c86a0ef8061e3b98ed9d3dcbac789f9430685c895fe51e63` |
| V3 area Unicode | PASS | PASS | `a2d26b5f591decc90548b8c4fe9b3cfd73c13430fe15c78775ba19ed5de0ee3c` |
| V4 label punctuation | PASS | PASS | `f695a6e4abc50d432623ac0602b4364c4178ba871dd3252197e566a55064d8b5` |
| V5 reference-kind separation | PASS | PASS | `343b9723b17bdad7c67468c684f681da799e5904eee641d7991c988e4547d899` |
| V6 different secret | PASS | PASS | `3de8a854565b19548e1c121c40acdceb951fafb51d05c2fb450ab45bd0db3264` |
| Version changed to 2 | PASS | PASS | `437ac43f235577a93164ee1e6f0edee44c94e10e001943b9fb59ce649c3401d5` |
| Domain changed with `-X` | PASS | PASS | `51a2a5cbbb6c7ec290b4d3db38c8300321d7c2c69ae1d94bc5f9ff1349e43009` |

The V1 message is 161 octets. Every expected digest decodes to 32 octets (256 bits), confirming no truncation.

As a non-normative review check, changing only the synthetic scope from 64 `a` characters to 64 `b` characters produced:

`7e10cb0bffd0787c0f35b2037ee28fa0ce0fc8ae034c5f2497a626cc5de8c619`

This confirms that scope participates in the defined message, while also supporting R004-F-003: the normative vector document does not itself publish this separation case.

## Security, privacy and lifecycle checks

- HMAC-SHA-256 is used as a keyed construction, not as an unkeyed or secret-prefix hash.
- Public scope and guessed raw identifiers are insufficient without the installation-local secret.
- Different secrets and reference kinds produce different authenticated inputs/results.
- Secret reuse across distinct installations is prohibited; preserved-secret migration intentionally preserves one privacy context.
- Raw production identifiers and secret material are prohibited in public output and logs.
- Missing, malformed, unavailable or non-canonical secret material fails closed.
- Secret loss does not silently regenerate identity; exact restore or separately governed reset is required.
- Rotation and normative-byte changes are identity-affecting and require snapshot boundaries/version separation.
- Historical and current formats may coexist only as separately versioned immutable artifacts, not as aliases or mixed current references.

## Open-decision closure audit

CA001-D-001 through D-014, D-016 and D-017 are either normatively resolved or explicitly bounded outside CA-001 where inherited governance requires later work. CA001-D-015 is not fully resolved because collision response is specified without collision detection scope. See R004-F-001.

## Mutation boundary

This review created only the three files in the authorized R-004 directory. It did not modify CA-001, governance, AI-002, DF-002, production code, tests, fixtures, dependencies, configuration or contracts.

