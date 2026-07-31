# R-003 Independent Test-Vector Verification

R-003 independently implemented `frame(s) = uint32_be(len(NFC(s).utf8)) || NFC(s).utf8`, then reconstructed all inputs twice without reading AI-001’s recorded PASS value.

Common raw UUID: `123e4567-e89b-42d3-a456-426614174000`  
Computed scope: `is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194`

| Category | Normalized key | Computed output | Match |
|---|---|---|---|
| `api_availability` | `ck1:api_availability:rest_api_root` | `obs1_90cbe1026ff98c538ec18854829293d38349ca802779bc8d362e948a9481dbcd` | PASS |
| `loaded_component` | `ck1:loaded_component:mqtt` | `obs1_79927229da53e5b9d0b9b2e503f769329d20e7a475285cb24553ee70e903e713` | PASS |
| `registered_event_type` | `ck1:registered_event_type:state_changed` | `obs1_864d18c0e05d48fc16c99ddd83fc371057b8b8612b0a4010ea6e02baa4046b79` | PASS |
| `entity_display_reference` | `ck1:entity_display_reference:ref1_entity_d26423e92d0995348b23e8a0bab951fd9696898a0230020d11896033125b0f92` | `obs1_2916c20e0c01a5b72588d693da87368aafdf654d80ab083eca3a0c26bb40b3c3` | PASS |

The exact API pre-hash bytes reproduced AI-001’s normative hexadecimal sequence. Other categories’ bytes decoded as four complete length-framed fields in the specified order; a change in any field changed the byte sequence.

Boundary verification:

- `custom:demo` → `custom%3Ademo`: PASS.
- decomposed and composed `café` → `caf%C3%A9`: PASS.
- case is preserved and changes identity: PASS.
- whitespace is preserved as `%20`, not trimmed: PASS.
- absent or empty required component: invalid, no vector: PASS.
- control-containing or unknown-category component: invalid: PASS.
- duplicate canonical key with identical payload collapses; conflicting payload invalidates capability: PASS.
- collision response rejects rather than suffixes: PASS.
- independent relationship calculation produced `rel1_0dcf6e930b21dd8104a1ce0a2b56ac5f095d3c9d4a0d3ffabf46e4d48772951c`; the bytes were unambiguous, though endpoint semantics fail compatibility review.

Independent identity-vector gate: **PASS**.

