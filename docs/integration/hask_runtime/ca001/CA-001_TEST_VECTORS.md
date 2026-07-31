# CA-001 Normative Synthetic Test Vectors

## Safety and conventions

All values are synthetic and prohibited for production use. Hexadecimal is lowercase. Message construction is exactly `CA-001_NORMATIVE_SPECIFICATION.md`.

Synthetic secret S1, raw octets `00` through `1f`:

`AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8`

Synthetic secret S2, raw octets `20` through `3f`:

`ICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj8`

Both are canonical unpadded Base64url encodings of 32 octets. Synthetic scope:

`is1_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

Domain hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d323536`

## Vector V1 — entity ASCII

- Secret: S1
- Kind: `entity`
- Raw identifier: `sensor.kitchen_temperature`
- Exact message hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d323536000000010000000300000006656e74697479000000446973315f616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161610000001a73656e736f722e6b69746368656e5f74656d7065726174757265`

- Expected HMAC-SHA-256:
  `312675c4bb1c9ddc1caffc38c97bf0bc686bfb45909d60cd0d629355a296352d`
- Expected public reference:
  `refh1_entity_312675c4bb1c9ddc1caffc38c97bf0bc686bfb45909d60cd0d629355a296352d`

## Vector V2 — device Unicode

- Secret: S1
- Kind: `device`
- Raw identifier Unicode sequence: `device-\u03b1` (Greek small alpha; UTF-8 `ce b1`)
- Exact message hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d323536000000010000000300000006646576696365000000446973315f61616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161000000096465766963652dceb1`

- Expected HMAC-SHA-256:
  `c4bb39925ca26b54c86a0ef8061e3b98ed9d3dcbac789f9430685c895fe51e63`
- Expected public reference:
  `refh1_device_c4bb39925ca26b54c86a0ef8061e3b98ed9d3dcbac789f9430685c895fe51e63`

## Vector V3 — area Unicode

- Secret: S1
- Kind: `area`
- Raw identifier Unicode sequence: `area.k\u00f8kken` (UTF-8 includes `c3 b8`)
- Exact message hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d32353600000001000000030000000461726561000000446973315f616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161610000000c617265612e6bc3b86b6b656e`

- Expected HMAC-SHA-256:
  `a2d26b5f591decc90548b8c4fe9b3cfd73c13430fe15c78775ba19ed5de0ee3c`
- Expected public reference:
  `refh1_area_a2d26b5f591decc90548b8c4fe9b3cfd73c13430fe15c78775ba19ed5de0ee3c`

## Vector V4 — label reserved punctuation

- Secret: S1
- Kind: `label`
- Raw identifier: `label:energy`
- Exact message hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d3235360000000100000003000000056c6162656c000000446973315f616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161610000000c6c6162656c3a656e65726779`

- Expected HMAC-SHA-256:
  `f695a6e4abc50d432623ac0602b4364c4178ba871dd3252197e566a55064d8b5`
- Expected public reference:
  `refh1_label_f695a6e4abc50d432623ac0602b4364c4178ba871dd3252197e566a55064d8b5`

## Vector V5 — reference-kind separation

S1 and raw identifier `device-\u03b1`, but kind `entity`, produce:

- Expected HMAC-SHA-256:
  `343b9723b17bdad7c67468c684f681da799e5904eee641d7991c988e4547d899`
- Expected public reference:
  `refh1_entity_343b9723b17bdad7c67468c684f681da799e5904eee641d7991c988e4547d899`

This differs from V2 because kind is authenticated.

## Vector V6 — different secret

V1 message with S2 produces:

- Expected HMAC-SHA-256:
  `3de8a854565b19548e1c121c40acdceb951fafb51d05c2fb450ab45bd0db3264`
- Expected public reference:
  `refh1_entity_3de8a854565b19548e1c121c40acdceb951fafb51d05c2fb450ab45bd0db3264`

## Vector V7 — installation-scope separation

V1 uses S1, kind `entity` and raw identifier
`sensor.kitchen_temperature`. Change only the synthetic installation scope to:

`is1_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`

Exact message hex:

`4841534b2f4841444f43532f4f50415155452d5245464552454e43452f484d41432d5348412d323536000000010000000300000006656e74697479000000446973315f626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262620000001a73656e736f722e6b69746368656e5f74656d7065726174757265`

- Expected HMAC-SHA-256:
  `7e10cb0bffd0787c0f35b2037ee28fa0ce0fc8ae034c5f2497a626cc5de8c619`
- Expected public reference:
  `refh1_entity_7e10cb0bffd0787c0f35b2037ee28fa0ce0fc8ae034c5f2497a626cc5de8c619`

This differs from V1 because installation scope is authenticated. Secret,
kind, raw identifier, format version, domain and framing are unchanged.

## Version and domain verification

Changing only `U32BE(version)` from `00000001` to `00000002` in V1 produces HMAC:

`437ac43f235577a93164ee1e6f0edee44c94e10e001943b9fb59ce649c3401d5`

This is not a valid v1 public reference because v1 validation requires version 1.

Changing only the domain to the synthetic non-v1 value ending `-X` produces HMAC:

`51a2a5cbbb6c7ec290b4d3db38c8300321d7c2c69ae1d94bc5f9ff1349e43009`

This is not a valid v1 result and verifies domain separation.

## Empty and negative cases

V1 permits no optional component. Therefore no valid empty-optional vector exists.

Reject before HMAC and emit no reference for:

- empty raw identifier;
- empty kind or scope;
- unknown, uppercase or aliased kind;
- scope not matching `is1_[0-9a-f]{64}`;
- component count other than 3;
- version other than 1 under `refh1_`;
- secret decoding to other than 32 octets;
- padded, whitespace-containing or non-canonical Base64url secret text;
- ill-formed Unicode or raw identifier containing prohibited control characters;
- truncated or uppercase output hex;
- public prefix kind differing from the authenticated kind;
- changed domain bytes while claiming v1.

All negative cases fail closed without raw identifier or secret disclosure.
