# AI-001 Privacy Analysis

| Component | Raw sensitivity | Public form | Reversible | Correlation |
|---|---|---|---|---|
| installation UUID | SENSITIVE local secret-like state | `is1_<sha256>` | No practical reversal | Same-installation snapshots correlate; cross-installation UUIDs differ |
| component/event identifier | LOCAL | percent-encoded canonical key component | Yes | Intended semantic correlation |
| entity/device/area/label ID | SENSITIVE | typed `ref1_…` digest scoped by public installation token | No practical reversal for non-enumerable values; entity IDs can be dictionary-guessed if scope is known | Limited to same installation |
| source capability | PUBLIC contract vocabulary | exact value | Not applicable | Intended |
| observation/relationship ID | PUBLIC pseudonymous token | `obs1_…` / `rel1_…` | No practical reversal | Same installation and object correlate |

No hostname, URL, IP address, location, account, username, email, credential, token, header, path or payload participates. User-visible names and labels are prohibited.

Because common entity identifiers may be guessable against a known public scope, source-reference hashes are pseudonymization rather than anonymity. They remain acceptable only for local output governed by the frozen privacy model; consumers must not publish or cross-installation aggregate them. Raw scope and raw identifiers never enter output or logs. Determinism does not require exposing protected inputs.

Privacy result: PASS for the proposed local-only contract, subject to R-003 review of the stated correlation boundary.

