# IM-001 Batch 2 Blocker Report

## Decision

**BLOCKED — no Batch 2 implementation was started.**

The frozen DB-001 physical catalogue is complete at the table/column/reference
inventory level, but it does not uniquely determine all executable CHECK,
trigger, and view semantics that Batch 2 is required to reproduce exactly.
Selecting those semantics in implementation would redesign or weaken the frozen
architecture, both of which IM-001 prohibits.

## Preservation preflight

The mandatory preflight completed before any Batch 2 write:

- active authority: `IM-001`;
- implementation authorization: true, limited by the explicit Batch 2 gate;
- Batch 1: complete; infrastructure tests **16 passed**;
- Batches 3–5: unauthorized;
- DF-002: unchanged general implementation baseline;
- DB-001: complete, frozen database implementation baseline;
- DB-001 expected and observed SHA-256:
  `676e5cca648bf894eb69c1329371819e272fade44eba5ff9130fc3d1d0491e79`;
- Batch 1 preservation-report SHA-256:
  `d5781b2f2ca102d160df6b7c312872af3e0c5c42a9ebc1d428e09d273d02c3ab`;
- Batch 1 final-report SHA-256:
  `24c4220adcefa34b4f7ba96b98f37a7cf14d57557129bc9d804a931ade285913`;
- active public contract: `hadocs-generic-metadata 1.0.0`;
- proposed contract 2.0.0: inactive;
- HADocs branch/HEAD: `main` /
  `590cc33a9762c4d22699f20c60d136ef2c4de00c`.

No preflight mismatch was found.

## Blocking ambiguity 1: executable closed-value domains

DB-001 section 62 defines `CHK` as a physical check role. Section 63 assigns
that role to many columns, and sections 55–56 require closed-value and
conditional-presence enforcement. The frozen document does not enumerate the
complete literal value sets or all allowed combinations needed to generate
deterministic SQLite CHECK expressions.

Affected families include at least:

- logical-installation, collision-registry, entity, relationship, context and
  identity-registration status fields;
- scan status, completeness, terminal-field presence and capability outcomes;
- observation taxonomy, authority, privacy, retention and permitted
  taxonomy/retention/privacy combinations;
- compatibility result/capability-outcome combinations;
- audit event/outcome and version/bundle validation states;
- migration status, recovery validation and terminal-field presence;
- clone classification, ambiguity and activation outcomes;
- secret/provenance validation and requested/result activation states;
- declaration/provenance integrity and availability states;
- relationship event kind/continuity and current-tuple conditional presence;
- tagged subject kinds and contribution/ordinal constraints.

Some domains are described by upstream architecture documents, but DB-001 does
not provide a closed physical mapping for every `CHK` token or specify which
external enum spelling is the canonical stored spelling. Batch 2 therefore
cannot prove expected-versus-actual constraint conformance or the required zero
deviations without making implementation choices.

## Blocking ambiguity 2: trigger transition semantics

DB-001 section 68 allocates trigger enforcement but does not provide complete
trigger predicates for the narrower mutable families:

- `installation_context`: which exact status/end-time update is the sole
  permitted supersession transition;
- `identity_registration`: which exact status/retirement update is permitted;
- `scan_run`: the complete set of terminal status values and conditional fields;
- `migration_attempt`: the complete set of terminal status values and
  conditional fields;
- terminal `scan_capability_outcome`: the precise point at which mutation becomes
  prohibited.

A trigger that forbids every update would conflict with the stated controlled
transitions. A trigger that permits a broader update would weaken LC-018,
LC-023, and the section 68 retention model. Neither interpretation is
authorized.

## Blocking ambiguity 3: LifecycleHistory view contract

DB-001 sections 54 and 68 state that LifecycleHistory remains a query/view and
must not become a table. The frozen physical catalogue contains no view
definition, stable physical view name, output-column catalogue, union/join
semantics, or ordering contract. The Batch 2 request additionally requires a
test proving LifecycleHistory is a view.

Creating a view now would require inventing its public/physical shape. Omitting
it would fail the requested schema-conformance gate. The two requirements cannot
be reconciled from the frozen text alone.

## Why implementation cannot safely continue

The requested acceptance criteria require all database-owned constraints,
accepted triggers, and accepted views with zero deviations. A schema containing
only generic non-empty/range checks would under-enforce DB-001. Choosing
unpublished literals or transition matrices would add architecture through
implementation. Both violate G-001, IM-001's frozen-architecture boundary, and
the explicit Batch 2 stop rule.

The 25 table names, 243 columns, 25 INTEGER primary keys, fixed foreign-key
directions, candidate-key semantics, 18 named secondary indexes, PRAGMA profile,
application ID, and eight dependency phases were not found contradictory. They
are insufficient by themselves to satisfy the complete Batch 2 acceptance
contract.

## Required resolution

A separately governed architecture clarification must freeze, at minimum:

1. canonical stored literals and complete allowed-combination matrices for every
   section 63 `CHK` field;
2. exact conditional-null/terminal rules;
3. exact permitted transition predicates for every narrow trigger family; and
4. whether LifecycleHistory is a physical SQLite view and, if so, its stable
   name, columns, source relations, row semantics, and ordering guarantees.

After that clarification is independently reviewed and incorporated into the
frozen database implementation baseline, Batch 2 can resume without redesign.

## Change and scope audit

- Production code changed: **0**.
- Tests or fixtures changed: **0**.
- Migration artifacts created: **0**.
- Schema/tables/indexes/triggers/views created: **0**.
- Repositories or business persistence created: **0**.
- Governance changed: **0**.
- DB-001 changed: **0**.
- Batch 1 artifacts changed: **0**.
- Batch 3–5 work started: **0**.
- New file: this blocker report only.
