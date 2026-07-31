# R-003 Canonical Key Review

AI-001 defines a closed `ck1:<category>:<component>` grammar, NFC normalization, UTF-8 byte encoding, uppercase percent escapes, case preservation, no trimming, required non-empty components and explicit invalid forms. Category boundaries are unambiguous because category is closed and the component encodes `:` and `%`. The four category component sources are explicit. Duplicate and conflicting values have deterministic behavior.

The format is public, implementation-independent and versioned by `ck1`. Its raw component privacy is acceptable for public component/event identifiers; entity keys contain only a typed opaque token, whose transformation is reviewed separately.

Canonical-key gate: **PASS**.

