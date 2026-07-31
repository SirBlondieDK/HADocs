# R-003 Observation ID Review

Normative tuple order is domain separator, public installation scope, source capability and canonical key. Every value is NFC-normalized, UTF-8 encoded and prefixed with an unsigned four-byte big-endian byte length. SHA-256 renders as 64 lowercase hexadecimal characters after `obs1_`; total output is 69 ASCII characters.

Framing is injective over the sequence of normalized byte strings: a decoder reads exactly four bytes of length then exactly that many value bytes, repeatedly. Therefore two distinct framed tuples cannot produce the same pre-hash byte sequence through separator ambiguity. NFC-equivalent strings intentionally normalize to the same bytes; all other tuple changes alter the pre-hash input.

Contract version is deliberately excluded and identity format is independently namespaced by `/v1` and `obs1_`. Collision behavior rejects the affected snapshot without suffix or order dependence.

Observation-ID gate: **PASS**.

