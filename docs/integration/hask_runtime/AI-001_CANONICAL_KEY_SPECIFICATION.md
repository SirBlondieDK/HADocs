# AI-001 Canonical Key Specification

## Contract

`canonical_key` is a non-empty UTF-8 string with grammar:

```text
canonical-key = "ck1:" category ":" component
category      = "api_availability" / "loaded_component" /
                "registered_event_type" / "entity_display_reference"
component     = 1*( unreserved / pct-encoded )
unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
pct-encoded   = "%" HEXDIG HEXDIG   ; uppercase A-F only
```

Construction is exactly:

1. Select the category-specific authoritative component.
2. Convert it to Unicode NFC without trimming or case folding.
3. Encode as UTF-8.
4. Preserve bytes for ASCII `A-Z a-z 0-9 - . _ ~`; encode every other byte as `%HH` with uppercase hex.
5. Concatenate ASCII `ck1:`, exact category, ASCII `:`, encoded component.

Whitespace is retained and percent-encoded. Empty component is invalid. Unicode control characters U+0000–U+001F and U+007F are invalid. Numeric and boolean components are not allowed in identity format 1; no formatting rule is therefore applicable. Optional identity components are prohibited. Missing components yield no observation. Aliases are prohibited.

## Category components

- `api_availability`: fixed ASCII `rest_api_root`.
- `loaded_component`: exact documented component string.
- `registered_event_type`: exact documented event-type string.
- `entity_display_reference`: the normative `ref1_entity_…` token derived from the raw entity identifier.

## Examples

- `ck1:api_availability:rest_api_root`
- `ck1:loaded_component:mqtt`
- `ck1:registered_event_type:state_changed`
- `ck1:entity_display_reference:ref1_entity_d26423e92d0995348b23e8a0bab951fd9696898a0230020d11896033125b0f92`
- Component `custom:demo` becomes `ck1:loaded_component:custom%3Ademo`.
- Component `café` becomes `ck1:loaded_component:caf%C3%A9` after NFC.

Invalid: uppercase percent hex policy violation `%3a`; missing component; unknown category; raw sensitive entity ID; leading/trailing trimming; non-NFC text; empty or control-containing source value.

The key remains stable until category, authoritative component or identity-format version changes. Equal normalized keys denote one identity; conflicting duplicate observations invalidate the affected capability.

