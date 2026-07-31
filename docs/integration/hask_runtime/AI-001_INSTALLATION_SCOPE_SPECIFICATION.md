# AI-001 Installation Scope Specification

## Meaning and creation

An installation is one logical Generic Metadata Collector identity domain, not a host, URL, Home Assistant address or account. On first initialization with no prior collector identity state, the collector creates one RFC 4122 UUID version 4 using a cryptographically secure random source with 122 random bits. The raw value is stored as lowercase canonical UUID text.

The raw UUID is persistent collector state. It is created once, written atomically, readable only by the collector identity, stored outside source/bundle/output directories, included in backup, and never emitted or logged.

## Public representation

Define `frame(s)` as four-byte unsigned big-endian length of NFC UTF-8 bytes followed by those bytes. Then:

```text
scope_digest = SHA-256(
  frame("hadocs-generic-metadata/installation-scope/v1") ||
  frame(raw_uuid_lowercase)
)
installation_scope = "is1_" || lowercase_hex(scope_digest)
```

Grammar: `is1_[0-9a-f]{64}`; length 68 ASCII bytes. It is safe for consumer visibility and logs but remains a correlatable installation pseudonym.

Test UUID `123e4567-e89b-42d3-a456-426614174000` yields:

`is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194`

## Lifecycle

- Restart, HA restart, host restart, patch update and configuration reload: preserve.
- Backup/restore to the same or replacement host: restore raw scope; preserve.
- Explicit installation migration: migrate raw scope; preserve.
- Clone intended as the same logical installation: preserve, accepting correlation.
- Clone intended as a new installation: before collection, explicitly create a new UUID; all observation IDs change.
- Reinstall with restored identity state: preserve. Clean reinstall without it: new installation and new IDs.
- Automatic rotation: prohibited.

Missing/corrupt scope after identity has previously existed prevents new snapshot activation with safe internal code `installation_scope_unavailable`; retain any last valid snapshot as explicitly stale. Never silently create a replacement. Scope collision is treated as a security incident requiring explicit rotation of one installation before further publication.

