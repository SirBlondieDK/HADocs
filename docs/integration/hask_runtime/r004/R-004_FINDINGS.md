# R-004 Findings

## Classification scale

- `CRITICAL`: defeats the inherited security/privacy objective or makes safe use impossible.
- `MAJOR`: leaves a normative, security, interoperability or identity-stability decision to implementation.
- `MINOR`: bounded documentation or verification incompleteness that does not by itself change the defined identity bytes.
- `NONE`: no finding.

## Findings register

| ID | Class | Affected document(s) | Finding | Consequence |
|---|---|---|---|---|
| R004-F-001 | **MAJOR** | `CA-001_OPEN_DECISIONS.md`; `CA-001_RECOMMENDED_ARCHITECTURE.md`; `CA-001_NORMATIVE_SPECIFICATION.md`; `CA-001_MIGRATION_AND_RECOVERY.md` | CA001-D-015 requires the collision *detection scope*, failure boundary and relationship consequences. The final specification defines a response only after unequal canonical tuples are known to have the same digest. It does not state whether detection is mandatory, which current or historical tuple population must be compared, what internal state enables comparison, or how long that state must exist. | Independent implementations can conform to the byte derivation while implementing no detection, current-snapshot-only detection or cross-snapshot detection. These choices have different failure and silent-reassignment behavior. This is an unresolved architecture decision and prevents acceptance. |
| R004-F-002 | **MINOR** | `CA-001_RECOMMENDED_ARCHITECTURE.md`; `CA-001_SECRET_LIFECYCLE.md` | The recommendation alternates between a secret “containing exactly 256 bits of cryptographically generated entropy” and the implementable requirement “32 random octets from a CSPRNG.” Exact entropy of one generated value is not a directly validated property; byte length, generation method and security strength are. | The normative lifecycle remains implementable because it fixes 32 octets and a CSPRNG. Terminology should eventually be made precise, but the wording does not change HMAC bytes or the current failure result. |
| R004-F-003 | **MINOR** | `CA-001_REQUIREMENTS.md`; `CA-001_TEST_VECTORS.md` | The requirements call for installation-separation testing. The vector set proves secret separation and authenticates one installation scope, but contains no normative vector changing only `installation_scope`. | The framing is still unambiguous and an independent synthetic scope-change calculation succeeds, but the normative suite does not directly pin this required separation dimension. |

## Counts

| Classification | Count |
|---|---:|
| CRITICAL | 0 |
| MAJOR | 1 |
| MINOR | 2 |
| NONE | 0 |

## Disposition

R004-F-001 triggers `FAIL` under the R-004 result rules. R-004 records findings only and makes no repair, replacement architecture or implementation recommendation.

