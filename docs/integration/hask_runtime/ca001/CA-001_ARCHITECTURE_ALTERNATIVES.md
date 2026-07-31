# CA-001 Cryptographic Architecture Alternatives

## Status and method

This document evaluates technically reasonable architecture families against the approved CA-001 decision criteria. It makes no recommendation, selects no project primitive, defines no normative byte layout and provides no test vector.

“Technically reasonable” here means an architecture that can use installation-local secret material, produce deterministic opaque references, support explicit domain separation, avoid public secret disclosure, operate offline and be specified interoperably. The candidate set covers direct keyed-hash/MAC families and a composed key-derivation-plus-MAC family with credible primary specifications.

## Inherited constraints

Every candidate must preserve the DF-002 requirements recorded in `CA-001_EXISTING_AUTHORITY.md`: secret-local-material participation, installation scoping, deterministic cross-snapshot joins, resistance to output-only source-identifier confirmation, collision resistance, no cross-installation correlation, no secret/raw identifier disclosure and fail-closed behavior.

The active contract remains `hadocs-generic-metadata 1.0.0`. Nothing below is adopted or activated.

## Candidate A — HMAC with SHA-256

HMAC is a standardized keyed message-authentication construction built over an approved hash function. A direct architecture would use one installation-local key and explicit purpose/reference-kind separation in the authenticated input.

Advantages:

- Long-standing standardized construction with broad multi-language availability.
- Fixed 256-bit output when used without truncation.
- Straightforward independent interoperability and synthetic-vector verification.
- Security analysis is separated from the underlying hash’s collision behavior more cleanly than a naive secret-prefix hash.

Disadvantages:

- Domain separation, framing and key lifecycle remain project architecture decisions.
- A single undifferentiated key would increase misuse and cross-purpose coupling unless the architecture defines separation.
- API defaults can encourage ad hoc string concatenation unless normative inputs are separately frozen.

Migration and operations: requires persistent installation-local key material and regeneration of all affected public references when that key rotates. Operational support is generally broad, but backup and recovery remain explicit project obligations.

Security characteristics: conventional MAC security with a 256-bit result; output truncation, if any, would reduce collision and forgery margins and would need separate justification.

## Candidate B — KMAC256

KMAC is the NIST-standardized keyed function based on cSHAKE. It supports a customization string as part of the standardized construction and can produce a selected output length.

Advantages:

- Native keyed design and native customization facility support purpose separation.
- Variable output length without defining an external truncation convention.
- Standardized encoding machinery reduces some ambiguity when used exactly as specified.
- Modern sponge-based design independent of the SHA-2/HMAC family.

Disadvantages:

- Less ubiquitous in common application runtimes than HMAC.
- Variable output requires CA-001 to choose and freeze a length.
- Customization does not eliminate the need to define canonical application inputs and lifecycle.
- Implementations may expose KMAC inconsistently or require additional dependencies.

Migration and operations: persistent secret handling is comparable to other direct keyed functions. Portability risk is driven more by implementation availability than by the standard. A transition to or from KMAC changes all derived public bytes.

Security characteristics: configurable output and standardized domain customization; security strength depends on KMAC variant, key strength and chosen output length.

## Candidate C — keyed BLAKE2b with a 256-bit result

BLAKE2 has a standardized keyed mode and configurable digest length. This candidate uses the keyed mode directly rather than inventing a secret-prefix convention.

Advantages:

- Keyed operation is part of the algorithm specification.
- High software performance on common 64-bit platforms.
- Variable digest size can meet a chosen public-token size without separate truncation.
- RFC specification and implementations exist across several languages.

Disadvantages:

- Keyed BLAKE2 APIs and parameter handling are less uniform than HMAC APIs.
- Application domain separation and canonical framing still require project rules.
- Choosing BLAKE2b versus other BLAKE2 variants is itself an architecture decision.
- Some regulated or constrained environments may prefer NIST-specific primitives.

Migration and operations: direct persistent-key model; rotation changes affected references. Cross-language verification must confirm identical parameterization, especially digest size and keyed-mode semantics.

Security characteristics: native keyed hashing with configurable output; the security claim must be bounded to the exact variant, key size and digest length eventually selected.

## Candidate D — keyed BLAKE3 with a 256-bit result

BLAKE3 specifies a keyed mode and extensible output. A direct architecture could use its keyed operation with separate application-level context handling.

Advantages:

- High performance and parallel scalability.
- Native keyed operation and arbitrary-length output.
- A compact modern design with an official public specification and test ecosystem.

Disadvantages:

- Not an IETF or NIST standard at the reviewed authority level.
- Shorter deployment history and narrower default runtime availability than HMAC.
- Dependency and long-term interoperability risk is higher in conservative environments.
- Extensible output and multiple modes increase the importance of exact mode and length selection.

Migration and operations: likely requires an explicit dependency in some runtimes, which CA-001 cannot authorize. Persistent-key and rotation consequences otherwise match direct keyed alternatives. A primitive change regenerates public references.

Security characteristics: native keyed mode with a 256-bit default-sized result; assurance and adoption posture differ from formally standardized candidates.

## Candidate E — AES-CMAC

CMAC is a NIST-standardized message-authentication construction based on a block cipher. With AES it yields a 128-bit tag before any truncation.

Advantages:

- Formal NIST standard with extensive availability in cryptographic modules.
- Useful where AES hardware or validated AES implementations are already mandatory.
- Deterministic fixed-size output and well-defined MAC construction.

Disadvantages:

- A 128-bit full output has a lower birthday collision margin than 256-bit alternatives for identity namespaces.
- Less natural fit for software-only metadata identity than hash-based keyed functions.
- Requires cipher-key handling and explicit application domain separation.
- Broad application libraries may expose HMAC more consistently than CMAC.

Migration and operations: persistent AES key lifecycle is required. Hardware-backed environments may benefit, while portable software deployments may gain little. Rotation changes all affected references.

Security characteristics: standardized 128-bit MAC output; collision-scale analysis for identity use must be explicit even when forgery security is otherwise acceptable.

## Candidate F — per-purpose key derivation followed by a standardized MAC

This is a composed architecture: one installation root secret derives purpose/reference-kind subkeys, and a separately standardized MAC produces the public reference. Both stages and their separation labels would need exact selection later.

Advantages:

- Strong separation between entity, device, area, label and future purposes.
- Limits accidental cross-protocol key reuse.
- A root secret can remain stable while derivation policy makes subkey scope explicit.
- Supports structured future evolution when versioned carefully.

Disadvantages:

- More normative choices and more opportunities for incompatible implementations.
- Requires two primitives or modes, two domain-separation layers and a clearer key hierarchy.
- Adds migration complexity if either derivation or MAC layer changes.
- May be unnecessary if a direct keyed construction already provides sufficient native customization.

Migration and operations: only a root secret need be persisted, but derivation-version changes regenerate affected references. Recovery and rotation must distinguish root-key rotation from derivation-policy migration.

Security characteristics: potentially strongest purpose isolation, but overall assurance depends on correct composition and exact normative separation of both stages.

## Comparative matrix

| Criterion | A: HMAC/SHA-256 | B: KMAC256 | C: keyed BLAKE2b | D: keyed BLAKE3 | E: AES-CMAC | F: derivation + MAC |
|---|---|---|---|---|---|---|
| Secret-local-material gate | Meets | Meets | Meets | Meets | Meets | Meets |
| Formal standardization | NIST | NIST | IETF RFC | Project specification | NIST | Depends on selected pair |
| Typical interoperability | Very broad | Moderate | Broad/moderate | Moderate | Broad in crypto modules | Depends on both layers |
| Native customization/domain facility | No | Yes | Parameter/input dependent | Mode/context dependent | No | Yes through derivation design |
| Output-size flexibility | Via justified truncation | Native | Native | Native | Limited by block size | Depends on MAC |
| Normative complexity | Low/moderate | Moderate | Moderate | Moderate | Moderate | High |
| Dependency risk | Low | Moderate | Low/moderate | Moderate/high | Low/moderate | Combined risk |
| Identity collision margin before truncation | 256-bit output | Configurable | Configurable | Configurable | 128-bit output | Depends on MAC |
| Rotation impact | Regenerate | Regenerate | Regenerate | Regenerate | Regenerate | Root or policy dependent |
| Migration complexity | Moderate | Moderate | Moderate | Moderate/high | Moderate | High |
| Operational key hierarchy | Single key unless extended | Single key/customization | Single key unless extended | Single key/mode | Single AES key | Root plus subkeys |

## Non-eligible approaches

The following are not retained as candidates because they fail mandatory inherited gates, not because of preference:

- Unkeyed hashing with public installation scope: already rejected by R003-F-001 because output holders can test guessable identifiers.
- Secret-prefix or secret-suffix use of an ordinary hash without a standardized keyed construction: security and interoperability depend on an ad hoc composition.
- Random per-reference salts: breaks deterministic cross-snapshot joins or requires exporting/persisting a mapping not authorized by the frozen model.
- Reversible encryption of raw identifiers: conflicts with the opaque, non-recoverable public-reference purpose and adds decryption/key-exposure consequences.
- Hostname, IP address, account identity or machine identifier as key material: violates privacy, portability and stability requirements.

## Migration and coexistence observations

Every eligible candidate produces architecture-specific public bytes. Moving between candidates, changing secret material, changing input framing or changing domain labels therefore changes derived references. No candidate can be adopted as a transparent implementation substitution. A later decision must specify format version, historical treatment, activation boundary and whether coexistence is permitted. This document does not decide those matters.

## Primary specifications reviewed

- [NIST FIPS 198-1, The Keyed-Hash Message Authentication Code](https://csrc.nist.gov/pubs/fips/198-1/final)
- [NIST SP 800-185, SHA-3 Derived Functions including KMAC](https://csrc.nist.gov/pubs/sp/800/185/final)
- [RFC 7693, The BLAKE2 Cryptographic Hash and MAC](https://www.rfc-editor.org/rfc/rfc7693.html)
- [BLAKE3 specification repository](https://github.com/BLAKE3-team/BLAKE3-specs)
- [NIST SP 800-38B, CMAC Mode for Authentication](https://csrc.nist.gov/pubs/sp/800/38/b/upd1/final)

## Batch conclusion

All candidates remain alternatives. **No preferred architecture is recommended and no primitive is selected as HASK project architecture.**
