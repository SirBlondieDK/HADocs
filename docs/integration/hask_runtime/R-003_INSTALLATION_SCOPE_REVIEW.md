# R-003 Installation Scope Review

The proposal defines a collector identity domain created from CSPRNG UUIDv4 state, persisted atomically outside source/output, backed up, migrated and never silently regenerated. Public grammar is `is1_[0-9a-f]{64}`. Restart, update, restore, corruption and missing-state behavior are explicit and prevent accidental reset.

The design avoids hostnames, addresses, accounts and secrets in public output. A UUIDv4 provides portable random identity, not deterministic reconstruction; preservation supplies continuity.

Defect: clone semantics depend on whether a clone is “intended” to be the same or new logical installation, but no authoritative declaration, lifecycle transition or required pre-publication control defines that intent. Independent implementations could preserve or rotate differently. This risks unintended shared identity or unintended reset.

The privacy transformation of downstream raw source identifiers also conflicts with DF-002 and is handled by the privacy gate.

Installation-scope gate: **FAIL**.

