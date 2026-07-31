# AI-002 Clone Analysis

## Status and non-normative boundary

This Batch 1A document inventories clone scenarios, evidence, ambiguity gates
and technically reasonable architecture strategies. It makes **no normative
classification, rotation, lifecycle, failure, implementation, source-reference,
removal or version decision**.

Terms such as “could”, “candidate”, “possible” and “may inform” describe the
decision surface for Batch 1B. They do not authorize behavior. Where current
authority does not determine an answer, the answer remains unknown.

## Inherited evidence boundary

| Inherited source | Evidence relevant to clone analysis |
|---|---|
| DF-002 Privacy Model | Opaque references are installation-scoped, require secret local material and must not permit cross-installation correlation. |
| AI-001 installation-scope proposal | Defines a persisted scope and distinguishes same-logical-installation migration from a new installation, but R003-F-002 found that the declaring authority and transition are undefined. |
| R003-F-002 | Clone intent is not self-proving; authoritative classification, safe unknown behavior and rotation semantics remain unresolved. |
| Accepted CA-001 | Secret and scope jointly affect public references. Exact secret preservation preserves derivation; secret change is identity-affecting. Hostname, address, path and machine ID do not participate in derivation. Copy classification remains outside CA-001. |
| CA-001 lifecycle/recovery | Ordinary restart/update must not rotate; exact restore can preserve continuity; missing secret fails closed; copied secret produces identical references; rotation is an explicit identity discontinuity. |
| AI-002 authority | C-002 must analyze copy, restore, migration, clone, concurrent-clone and unknown-classification cases without using hostname, IP address, timestamp-only or random per-process identity as authority. |

## Evidence vocabulary

Reliability below means reliability for the stated fact, not authority to decide
logical-installation intent.

| Evidence class | What it can establish | Reliability limits |
|---|---|---|
| Exact persisted installation scope | Two states contain the same public-scope source state | Does not establish whether the copy is an approved migration, restore, standby or unintended clone. |
| Exact CA-001 secret-generation continuity | Two states can derive the same protected references for equal canonical inputs | Secret equality is sensitive and cannot be exposed for comparison; equality still does not establish intent. |
| Complete protected identity-state provenance | A recorded lineage may connect creation, backup, restore or migration operations | Authority, authenticity, replay handling and ownership of that provenance are not yet defined. |
| Explicit operator/deployment declaration | Intended same/new logical-installation treatment | Reliability depends on authenticated authority, timing and conflict handling, all still open. |
| Hypervisor/container/image operation metadata | A technical copy, clone, restore or relocation operation occurred | Platform-specific, may be missing after export/import, and does not determine intended logical identity. |
| Hardware/environment attributes | A host component or environment changed | Mutable, replaceable, virtualized and copyable; inherited authority prohibits several from determining identity. |
| Simultaneous activity evidence | More than one environment appears to use one identity context | Air gaps, delayed snapshots, unavailable coordination and false absence limit completeness. |
| Absence of prior identity state | Current storage lacks preserved identity state | Cannot prove whether state is genuinely new, lost, omitted or deliberately removed. |

No public reference, raw identifier, secret value, hostname, address, MAC
address, account identifier or machine identifier becomes authoritative clone
evidence merely because it is observable.

## Scenario inventory

The “determinable?” column concerns clone/logical-continuity classification from
currently identified evidence. It does not prescribe an outcome.

| Scenario | Observed inputs | Available evidence | Authoritative evidence currently established | Reliability | Ambiguity risks | Possible architectural consequences (not selected) | Determinable? | Ambiguity gate? |
|---|---|---|---|---|---|---|---|---|
| VM clone | Copied virtual disks/configuration; possibly new VM metadata | Hypervisor clone record, copied scope/secret state, operator intent, concurrent activity | Exact copied identity state proves shared derivation context only | HIGH for copying; LOW for intent | Full clone and migration can look identical; hypervisor metadata may be absent | Candidate preserve, rotate, quarantine or fail-closed paths | Conditional only | YES |
| LXC clone | Copied root filesystem/container configuration | Container-manager operation record, copied identity state, declaration | Same as VM clone | HIGH for local copy record; LOW/MEDIUM for intent | Export/import can remove lineage; host/container IDs are mutable | Same candidate paths as VM clone | Conditional only | YES |
| Snapshot restore | Earlier storage state replaces current state | Snapshot lineage, restore operation, secret/scope generation markers, current history | Exact restored state can establish return to an earlier cryptographic context | HIGH for state equality; LOW for whether another descendant is active | Restore may fork history or roll back collision/provenance state | Candidate continuity, rollback rejection, fork classification or gated recovery | Not from state alone | YES |
| Backup restore | Protected backup imported into an environment | Backup identity/provenance, operator declaration, destination state, source retirement evidence | CA-001 permits exact-secret restore when continuity is intended | HIGH for valid backup contents; intent authority undefined | Same backup may be restored repeatedly; source may remain active | Candidate migration/restore continuity or new-installation separation | Conditional only | YES |
| Full disk restore | Bitwise/system-level image restored | Image lineage, preserved identity state, deployment record | Preserved bytes prove context equality | HIGH for byte continuity | Indistinguishable from disk clone without operation provenance | Candidate continuity or clone gate | No, absent trusted provenance | YES |
| Hardware replacement | Identity storage moved/restored to substantially different hardware | Maintenance/migration declaration, preserved state, old-system retirement evidence | CA-001 excludes hardware identity from derivation and allows approved host migration continuity | MEDIUM/HIGH for preserved context; authority for approval open | Legitimate migration and concurrent duplicate may have same local evidence | Candidate continuity if migration authority is valid; otherwise gate | Conditional only | YES |
| Motherboard replacement | Board/platform identifiers change | Service record, preserved local identity state | Board identifiers are not derivation inputs | LOW as clone evidence | Virtualization and repair can mimic replacement; identifier may be unavailable | Candidate no identity effect or migration review | Clone status not determined by change | YES if used to infer continuity |
| CPU replacement | Processor attributes change | Hardware inventory, maintenance record | CPU is not a cryptographic identity input | LOW | CPU attributes can vary under VM scheduling and upgrades | Candidate no identity effect | No clone conclusion | NO as sole evidence; YES if classification attempted |
| NIC replacement | Network adapter identity changes | Hardware inventory, maintenance record | NIC identity is not a cryptographic identity input | LOW | Adapter changes are ordinary maintenance and easy to virtualize | Candidate no identity effect | No clone conclusion | NO as sole evidence; YES if classification attempted |
| MAC-address change | One or more link-layer addresses change | Runtime/network inventory | AI-002 explicitly prohibits MAC/host-derived identity logic by implication of machine/address prohibitions; CA-001 excludes host/address data from derivation | LOW | Randomization, virtualization, replacement and manual configuration | Candidate no identity effect | No clone conclusion | NO as sole evidence |
| Hostname change | Host label changes | Runtime configuration/history | CA-001 excludes hostname from derivation; AI-002 prohibits hostname-based classification | LOW | Rename is common and copyable | Candidate no identity effect | No clone conclusion | NO as sole evidence |
| OS reinstall | Operating system replaced, with or without restored identity storage | Install/restore record, presence and provenance of identity state | Preserved exact context can reproduce identity; absence cannot prove intentional newness | MEDIUM | Clean reinstall, state loss and deliberate reset can look identical | Candidate continuity with restored state, new context, or fail-closed recovery | Conditional only | YES |
| Fresh installation | No recognized prior collector identity state | Creation transaction, deployment declaration, absence of restoration lineage | Atomic first creation can establish a new local cryptographic context | HIGH for new state creation; LOW for historical intent | “Fresh” may actually be a restore missing identity files | New-context candidate; possible recovery gate if prior existence evidence exists | Conditional only | YES when prior provenance is unknown |
| Image deployment | Prebuilt image instantiated once or many times | Image manifest, first-boot state, deployment metadata | A clean image without copied identity state can create independent contexts; copied state proves shared context | MEDIUM/HIGH if image provenance is trusted | Image may accidentally contain scope/secret/collision registry | Candidate reject contaminated image, initialize new context or require declaration | Conditional only | YES |
| Golden image deployment | Template intentionally produces multiple systems | Template provenance, identity-state presence scan, per-instance declaration | Reused secret/scope proves shared context; absence permits but does not itself guarantee correct per-instance creation | HIGH for inspected template; future drift possible | Embedded state can create mass correlation; deployment metadata may be incomplete | Candidate enforce identity-state absence or explicit per-instance separation | Conditional only | YES |
| Test environment copy | Production-like or standalone state copied for testing | Copy record, environment designation, isolation record, copied identity state | Copied context proves correlation capability, not whether preservation is authorized | MEDIUM | Test labels are mutable; test may later connect or publish | Candidate mandatory separation, quarantine or explicitly non-publishing copy | Not from local state alone | YES |
| Production-to-test copy | Production storage/backup restored into test | Backup lineage, environment declaration, network/publication controls | Same as test copy; sensitive identity context may be duplicated | HIGH for documented restore; authority for outcome open | Source remains active by design; air gap may later end | Candidate separate identity, prohibit publication or gated transformation | Usually identifiable as copy if provenance exists; outcome unresolved | YES |
| Concurrent cloned systems | Two systems use the same scope/secret context concurrently | Shared coordination, duplicate publication, signed lineage, operator reports | Same context can produce same references; CA-001 prohibits secret reuse across distinct installations | Variable; absence of observation is weak | Network partitions, identical outputs and asynchronous scans impede detection | Candidate fail-closed, quarantine one/both, or require authoritative winner | Sometimes detectable, never reliably excluded locally | YES |
| Air-gapped clone | Copied system operates without coordination path | Local copied state, physical/deployment record, later reconciliation | Local equality proves copied context if securely compared; absence of concurrency evidence proves nothing | LOW/MEDIUM | No online lease or duplicate detection can establish uniqueness | Candidate explicit offline declaration, pre-separation or delayed activation | Not automatically | YES |
| Secret loss | Secret unavailable while other state may remain | Storage error, backup availability, prior-generation provenance | CA-001 requires fail-closed and prohibits silent regeneration | HIGH for validated unavailability | Loss can be confused with path/permission failure; does not itself prove clone | Candidate recovery-only state; clone classification separate | Secret condition yes; clone status no | YES for any identity reset decision |
| Secret regeneration | New secret appears after prior generation | Generation provenance, old/new generation markers, explicit authority record | CA-001 treats secret change as identity-affecting and prohibits automatic regeneration | HIGH if generation history is trustworthy | Unauthorized regeneration may masquerade as new installation or rotation | Candidate reject, classify discontinuity or require reset authority | Event may be detectable; legitimacy unresolved | YES |
| Secret migration | Exact secret intentionally transferred | Protected migration record, source retirement evidence, generation identity | CA-001 permits exact transfer for intended continuity; copy creates equal references | HIGH for exact protected transfer; source retirement uncertain | Transfer and copy are indistinguishable without lineage/retirement evidence | Candidate continuity, clone gate or separation | Conditional only | YES |
| Storage migration | Persistent volumes/filesystems relocated | Storage operation record, byte-identical identity state | Storage path does not affect CA-001 derivation | HIGH for state continuity | Copy may leave original mounted/active; path change alone proves little | Candidate continuity if relocation, clone gate if duplicate | Conditional only | YES when original disposition unknown |
| Container migration | Container state moves between hosts | Orchestrator migration event, preserved volume, source termination evidence | Host does not define identity; preserved context can maintain derivation | MEDIUM/HIGH | Reschedule, live migration, scale-out and clone can share surface signals | Candidate continuity for single-instance move or gate for scale-out | Conditional only | YES |
| Hypervisor migration | VM execution moves while disk/state remains one logical instance | Migration event, shared-storage ownership, source termination | Host/hypervisor location is not derivation input | MEDIUM/HIGH | Live migration failure may leave split-brain; metadata may be unavailable after import | Candidate continuity or split-brain gate | Conditional only | YES for uncertain completion |
| Unknown provenance | Identity state exists but lineage/intent cannot be established | Current scope/secret generation status only; possibly no operation history | Current cryptographic validity can be checked; logical uniqueness cannot | HIGH for local validity, NONE for provenance | Could be original, migration, restore, clone, stolen copy or partial recovery | Candidate preserve, rotate, quarantine or fail-closed strategies all have different costs | NO | YES — mandatory analysis gate |

## Cross-scenario ambiguity inventory

| Ambiguity | Why observation is insufficient | Decision required in Batch 1B |
|---|---|---|
| Copy versus move | Local bytes do not show whether the source was retired | Define acceptable authority/evidence for continuity and source retirement. |
| Restore versus fork | A snapshot/backup can restore one system or create several descendants | Define lineage/fork classification and behavior when descendants may coexist. |
| Same logical installation versus new installation | This is an intent/governance property, not a property of HMAC, scope or hardware | Define who may declare it, when, with what evidence and conflict handling. |
| Valid local context versus globally unique active context | Local validation cannot prove no air-gapped or partitioned duplicate exists | Define whether uniqueness is required, how uncertainty is represented and the safe activation boundary. |
| Planned migration versus unauthorized copy | Exact secret transfer looks identical at the destination | Define authenticated migration authority and provenance requirements. |
| Missing state versus intentionally fresh state | Absence can result from new install, deletion, incomplete backup or corruption | Define prior-existence evidence and the unknown-state gate. |
| Hardware/environment drift versus identity transition | Hardware, hostname and addresses may change without logical identity change | Explicitly decide their non-authoritative/secondary role without making them identity roots. |
| Concurrent duplicate detection | No single local signal reliably proves or disproves another active copy | Define optional evidence, false-negative boundary and deterministic unknown outcome. |
| Secret rotation versus installation rotation | Secret, public scope and downstream IDs have related but distinct effects | Define the allowed transition combinations and atomic boundary. |
| Historical continuity after separation | Old and new contexts cannot be silently aliased, but history may need lineage | Define non-secret provenance without exposing a raw mapping or claiming identity equivalence. |

Every ambiguity above requires an explicit Batch 1B disposition. This analysis
does not supply that disposition.

## Required architectural decision inventory

Batch 1B will need to decide, subject to authority and without inference:

1. The exact definition of clone, migration, restore, replacement and fresh
   installation.
2. The authority permitted to classify each transition.
3. The minimum evidence and timing for an authoritative declaration.
4. Whether classification may be automatic, explicit or a bounded combination.
5. The deterministic state when classification is absent, conflicting, stale or
   unverifiable.
6. Whether and how concurrent-use evidence affects classification.
7. Which events preserve or change scope, secret generation, references,
   observation IDs and relationships.
8. Whether secret and installation-scope rotation are coupled or separable.
9. The atomic transition/snapshot boundary.
10. Audit/provenance requirements that do not expose secrets or machine-derived
    identity.
11. Recovery after accidental clone or incomplete migration.
12. Air-gapped and split-brain behavior where uniqueness cannot be observed.
13. Historical lineage rules without aliasing old and new public identities.
14. Exact failure classification and safe output boundary.

These are decision requirements, not decisions made here.

## Technically reasonable classification strategies

No strategy is selected. A later specification could combine eligible elements
only if authority supports the composition and makes precedence unambiguous.

### Strategy A — Explicit authorized transition declaration

Classification would be driven by an authenticated, auditable declaration of
“continuity/migration” or “new installation/separation” before activation.

Advantages:

- Directly addresses intent rather than inferring it from hardware.
- Can cover air-gapped and production-to-test operations.
- Compatible with CA-001's explicit rotation/reset boundary and DF-002's
  deterministic requirement.

Disadvantages and gaps:

- Requires a still-undefined authority, authentication model, timing and
  conflict process.
- Human/deployment error can produce incorrect declarations.
- Cannot by itself prove the source stopped operating.

### Strategy B — Protected lineage/provenance state

Classification would use durable private records linking creation, backup,
restore, migration, secret generation and scope generations.

Advantages:

- Supports deterministic historical reasoning and rollback/fork detection.
- Can distinguish an acknowledged transition from unexplained state appearance.
- Compatible with CA-001's private provenance and snapshot boundaries.

Disadvantages and gaps:

- Copying provenance can copy the same claim to several descendants.
- Authenticity, replay, retention, corruption and recovery require additional
  exact rules.
- Does not independently establish source retirement or intent.

### Strategy C — Deployment/platform operation attestation

Classification would consume trusted hypervisor, container, backup or
deployment-system evidence of clone, move, restore or image instantiation.

Advantages:

- Can capture operation semantics near the event.
- Reduces manual classification in managed environments.
- May identify golden-image and repeated-restore patterns.

Disadvantages and gaps:

- Platform-specific and unavailable in unmanaged or air-gapped installations.
- Import/export may strip evidence.
- Technical operation type still may not express logical-installation intent.

### Strategy D — Active uniqueness/lease coordination

A shared coordination mechanism would attempt to detect concurrent use of one
identity context.

Advantages:

- Could detect some split-brain and concurrent clones while connected.
- Can provide current evidence beyond static lineage.

Disadvantages and gaps:

- Conflicts with local-only/offline expectations if made mandatory.
- Cannot prove uniqueness during partitions or air gaps.
- Introduces availability, ownership and recovery semantics not currently
  authorized.
- Absence of a conflict is not proof of uniqueness.

### Strategy E — Conservative unknown-state gate

Unclassifiable provenance would enter a bounded non-publishing or fail-closed
state pending authorized classification.

Advantages:

- Avoids silently preserving or rotating identity on weak evidence.
- Aligns with G-001's ambiguity blocker principle and CA-001 fail-closed posture.
- Does not require hardware-derived identity.

Disadvantages and gaps:

- Can reduce availability after legitimate restores or migrations.
- Requires exact recovery and stale-snapshot behavior.
- The threshold for “unknown” must be normative to avoid implementation drift.

### Strategy F — Always preserve copied identity state

Any valid restored/copied scope and secret would be treated as continuity.

Advantages:

- Simple and maximizes cross-snapshot continuity.
- Matches byte-level reproducibility for approved migrations.

Disadvantages and compatibility risks:

- Concurrent clones intentionally correlate and collide in identity space.
- Conflicts with DF-002's cross-installation non-correlation when copies are
  distinct installations.
- Does not resolve R003-F-002's intent/authority defect.

### Strategy G — Always rotate after copy/restore evidence

Any detected restore, copy or host transfer would receive a new identity
context.

Advantages:

- Strongly separates duplicated environments.
- Avoids same-context concurrent publication when detection is correct.

Disadvantages and compatibility risks:

- Breaks approved migration, replacement-host and disaster-recovery continuity.
- Operation evidence can be missing or falsely triggered.
- Contradicts CA-001's prohibition on automatic rotation for ordinary restore
  unless separately authorized.

### Strategy H — Environmental fingerprint classification

Hardware, MAC address, hostname, machine ID or similar attributes would drive
same/new-installation classification.

Advantages:

- Signals are often locally observable.
- May detect some copied environments without external coordination.

Disadvantages and compatibility risks:

- Mutable, virtualized, spoofable and frequently changed during legitimate
  maintenance.
- Copies may retain them; migrations may change them.
- Inherited authority explicitly excludes several from identity derivation and
  prohibits hostname/IP/timestamp-only clone classification.
- Cannot serve as the sole authoritative strategy under current constraints.

## Comparative matrix

| Strategy | Determines intent directly | Air-gap capable | Preserves valid migration | Detects concurrency | DF-002 fit | CA-001 fit | Principal unresolved gate |
|---|---:|---:|---:|---:|---|---|---|
| A Explicit declaration | Potentially | Yes | Potentially | No | Potentially compatible | Compatible if transition is explicit | Authority/authentication/conflict rules |
| B Protected lineage | Partially | Yes | Potentially | Not alone | Potentially compatible | Compatible with private provenance | Copy/replay/authenticity |
| C Platform attestation | Partially | Sometimes | Potentially | Sometimes | Environment-dependent | Does not change cryptography | Portability and semantic authority |
| D Active coordination | No | No | Potentially | Partially | Risk if mandatory | Orthogonal to derivation | Offline/partition semantics |
| E Unknown-state gate | No | Yes | Only after resolution | No | Strong safety alignment | Strong fail-closed alignment | Availability and recovery authority |
| F Always preserve | No | Yes | Yes | No | Conflicts for distinct copies | Byte-compatible but clone-unsafe | Cross-installation correlation |
| G Always rotate | No | Yes | No | Not required | Breaks continuity | Conflicts with ordinary-restore rule | False rotation and history discontinuity |
| H Environmental fingerprint | No | Yes | Unreliable | Unreliable | Weak/incompatible as sole authority | Inputs excluded from derivation | Mutability/spoofing/privacy |

The matrix compares consequences only. It does not rank or choose a strategy.

## Evidence gaps and ambiguity gates for Batch 1B

| Gate | Evidence required before a normative decision | Current state |
|---|---|---|
| Classification authority | Existing governance/source evidence supporting who may declare continuity or separation | UNRESOLVED |
| Declaration authenticity | Evidence that a declaration can be bound to the relevant transition without exposing secrets | UNRESOLVED |
| Source retirement | Evidence sufficient to distinguish move from copy | UNRESOLVED |
| Offline uniqueness | Evidence model for air-gapped or partitioned copies | UNRESOLVED; automatic proof may be impossible |
| Provenance integrity | Authority for creation, retention, replay and corruption handling | UNRESOLVED |
| Unknown-state behavior | Frozen lifecycle basis for safe, deterministic treatment | PARTIALLY BOUNDED by fail-closed principles; exact outcome unresolved |
| Scope/secret coupling | Exact transition combinations consistent with CA-001 | UNRESOLVED in clone context |
| Historical lineage | Non-secret method to record discontinuity without aliasing identities | UNRESOLVED |

Batch 1B must stop rather than invent a rule if these gates cannot be resolved
from inherited authority. This document does not claim that all gates are
resolvable.

## Compatibility summary

### Accepted CA-001

Compatible future strategies would need to preserve CA-001's fixed HMAC
construction, explicit secret lifecycle, no automatic ordinary-restore
rotation, atomic snapshot boundaries, no secret/raw-ID disclosure and
identity-affecting treatment of secret/scope changes. Clone analysis does not
alter any of those rules.

### DF-002

Compatible future strategies would need deterministic installation-scoped
identity, stable authorized continuity, non-correlation between distinct
installations, fail-closed unsafe handling and no hardware/environment inference
that weakens privacy. This analysis does not amend DF-002.

## Batch 1A conclusion

All requested scenarios, evidence surfaces, ambiguity risks and technically
reasonable strategy families have been inventoried. The central unresolved fact
is that copied cryptographic state proves shared derivation context but does not
prove whether the copy represents continuity, migration, restore, standby or a
distinct installation.

**NORMATIVE_DECISIONS_MADE: 0**

Batch 1B may begin only under the existing AI-002 authority after applying the
G-002 resume procedure and must consume this analysis without treating any
candidate strategy as selected.

