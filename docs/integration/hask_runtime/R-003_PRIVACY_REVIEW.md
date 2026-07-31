# R-003 Privacy Review

| Component | Public form | Principal risk |
|---|---|---|
| Raw UUIDv4 | `is1_` SHA-256 token | stable local pseudonym; no practical UUID preimage |
| Component/event ID | canonical percent-encoded text | intended semantic visibility |
| Entity/device/area/label ID | public-scope keyed `ref1_` SHA-256 | dictionary testing of low-entropy identifiers |
| Observation/relationship tuple | `obs1_` / `rel1_` digest | same-installation correlation |

AI-001 excludes credentials, URLs, addresses, names, email, location, payloads and raw installation/source IDs. Its transformations are deterministic and portable when scope state is preserved.

Critical compatibility defect: DF-002’s frozen privacy model requires opaque references to be non-reversible **without secret local material** and states that the secret material remains outside artifacts and logs. AI-001 uses the public `installation_scope` as the only scope input. Anyone holding output can test common entity IDs and confirm matches. AI-001 acknowledges this but labels it acceptable without authority to relax the frozen guarantee. This is a privacy-treatment change, not an editorial note.

Privacy gate: **FAIL**.
