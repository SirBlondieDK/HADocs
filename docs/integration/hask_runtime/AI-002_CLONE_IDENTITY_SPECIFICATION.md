# AI-002 Clone Identity Specification

## 1. Purpose

### 1.1 Normative scope

This document normatively closes AI-002 Correction C-002 / R003-F-002. It
defines logical-installation clone classification, evidence authority,
deterministic decision precedence, ambiguity handling, continuity/discontinuity
effects and private provenance requirements.

The key words `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`,
`SHOULD NOT` and `MAY` are normative.

### 1.2 Inherited authority

- DF-002 remains the implementation baseline and retains four capabilities,
  four categories, four predicates and active contract 1.0.0.
- AI-001 supplies the frozen canonical-key, source-capability and observation-ID
  constructions except for direct corrected identity inputs.
- R003-F-002 requires authoritative clone classification, deterministic unknown
  handling and exact continuity/discontinuity effects.
- Accepted CA-001 supplies the complete cryptographic secret, reference,
  collision, snapshot, migration and recovery architecture and is not redefined.
- The Clone Analysis supplies scenario/evidence inventory.
- The Clone Decision Record supplies the accepted design rationale: explicit
  declaration plus protected lineage plus a conservative ambiguity gate, with
  platform/concurrency evidence only corroborative.

### 1.3 Out of scope

This specification does not define or change:

- HMAC-SHA-256, CA-001 framing, domain, secret format or collision behavior;
- canonical-key grammar or source-capability vocabulary;
- relationship `source_ref` representation;
- removal versus `IDENTITY_INVALID` semantics;
- contract-version selection or activation;
- storage technology, UI, API, network protocol or implementation classes;
- production code, tests, fixtures or runtime behavior.

## 2. Definitions

### 2.1 Logical installation

A **logical installation** is one governed collector identity lineage with one
current installation scope and one current CA-001 secret generation. It is not
defined by host, VM, container, hardware, hostname, address, account, path,
clock or process.

### 2.2 Clone

A **clone** is an independently activatable copy of identity-bearing state for
which the original lineage has not been authoritatively retired as part of one
continuity transition. Copy mechanics alone do not establish whether a copy is
a clone; authoritative declaration and protected provenance do.

### 2.3 Migration

A **migration** is an authoritatively declared continuity transition that moves
one logical installation to a successor environment, binds the successor to the
same lineage and records retirement of the predecessor before successor
publication. A copy without those elements is not a migration under this
specification.

### 2.4 Restore

A **restore** reconstructs state from an earlier protected snapshot or backup.
Restore is an operation type, not a clone classification. It becomes continuity,
separation or unknown only through the decision model.

### 2.5 Replacement

A **replacement** changes a host or host component while intending one logical
installation to continue. Component change alone is not authoritative; full
host replacement uses the same continuity evidence as migration.

### 2.6 Fresh installation

A **fresh installation** is a first initialization with no inherited identity
state, no prior-existence marker and protected provenance recording local first
creation. Missing, deleted, unreadable or incompletely restored state is not by
itself a fresh installation.

### 2.7 Concurrent clone

A **concurrent clone** exists when authoritative or supporting evidence proves
that two independently active environments are using the same installation
scope and CA-001 secret generation without one being a completed, retired
predecessor in a continuity transition.

### 2.8 Unknown classification

`UNKNOWN` is the required classification when evidence is absent, incomplete,
unverifiable, stale, replayed, contradictory or insufficient to establish
exactly one of `SAME_LOGICAL_INSTALLATION` or
`DISTINCT_LOGICAL_INSTALLATION`. `UNKNOWN` is not evidence of a clone and is not
permission to infer continuity or separation.

## 3. Authority model

### 3.1 Closed evidence classes

#### Authoritative declaration

An **authoritative declaration** is a private, explicit statement made by the
configured identity authority before activation. It SHALL declare exactly one
intent:

- `CONTINUITY`, identifying one predecessor lineage and asserting predecessor
  retirement; or
- `SEPARATION`, declaring a distinct logical installation.

The **identity authority** is the locally configured administrative principal
responsible for the collector identity transition. It MUST be recognized by the
producer's existing protected administrative trust boundary. The producer MUST
NOT infer, self-create or upgrade a declaration from environmental evidence.

#### Protected provenance

**Protected provenance** is the private, durable, integrity-checked lineage
record defined in Section 7. It SHALL bind declarations, predecessor lineage,
scope generation, secret generation and transition outcome without exposing
secret material.

#### Supporting evidence

**Supporting evidence** is non-authoritative information that may corroborate
or contradict a declaration/provenance pair. It MUST NOT create continuity or
separation by itself.

#### Platform attestation

**Platform attestation** is supporting evidence from a hypervisor, container,
backup, image or deployment system that an operation such as copy, move,
restore or instantiation occurred. It is never authoritative identity intent.

#### Concurrency evidence

**Concurrency evidence** is positive evidence that more than one independently
active environment uses the same identity context. Positive validated evidence
is contradiction evidence. Absence of concurrency evidence has no affirmative
meaning.

### 3.2 Precedence

Evidence SHALL be evaluated in this exact order:

1. CA-001 local-state validity and provenance integrity failure.
2. Positive validated concurrency conflict.
3. Conflicting, replayed, stale or non-authoritative declaration.
4. Valid `SEPARATION` declaration plus matching provenance.
5. Valid `CONTINUITY` declaration plus matching provenance and predecessor
   retirement assertion.
6. Valid protected first-creation provenance for a fresh installation.
7. All other evidence states.

Steps 1 through 3 produce `UNKNOWN` with `FAIL_CLOSED`. Step 4 produces
`DISTINCT_LOGICAL_INSTALLATION` with `NEW_CONTEXT_REQUIRED`. Step 5 produces
`SAME_LOGICAL_INSTALLATION` with `PRESERVE_CONTEXT`. Step 6 produces
`DISTINCT_LOGICAL_INSTALLATION` with `NEW_CONTEXT_REQUIRED`. Step 7 produces
`UNKNOWN` with `FAIL_CLOSED`.

A lower-precedence item MUST NOT override a higher-precedence result.

### 3.3 Evidence permitted to support a decision

- A valid authoritative declaration and matching protected provenance MAY
  establish continuity or separation under the precedence model.
- Platform attestation MAY corroborate operation type or contradict a declared
  transition.
- Positive concurrency evidence MAY contradict continuity.
- Protected backup, restore and predecessor-retirement records MAY corroborate
  lineage.
- Hardware/environment changes MAY be recorded only as non-authoritative
  operational context when privacy permits.

### 3.4 Evidence prohibited from independently determining identity

The following MUST NOT independently establish continuity, separation, clone,
migration, restore classification or freshness:

- copied scope, secret, collision registry or other identity bytes;
- VM/container/image identifiers;
- motherboard, CPU, NIC or other hardware identifiers;
- MAC address, IP address, hostname, machine ID, account or path;
- timestamp, boot time or elapsed time;
- platform operation label or deployment tag;
- absence of observed concurrent activity;
- absence of identity state;
- random process/runtime values;
- consumer assertion.

## 4. Decision model

### 4.0 Evaluation trigger

The clone decision model SHALL be invoked before activation when identity-bearing
state is created, copied, restored, migrated, regenerated or found with missing,
conflicting or discontinuous provenance. It SHALL also be invoked when positive
same-context concurrency evidence is validated.

The model MUST NOT be invoked solely because motherboard, CPU, NIC, MAC address,
hostname, IP address, machine identifier, path or other environmental data
changed while the existing CA-001 context and protected lineage remain valid and
uninterrupted. Such a change retains the already established classification.

### 4.1 Closed results

Every evaluation SHALL return exactly one classification and one activation
outcome.

Classifications:

- `SAME_LOGICAL_INSTALLATION`
- `DISTINCT_LOGICAL_INSTALLATION`
- `UNKNOWN`

Activation outcomes:

- `PRESERVE_CONTEXT`
- `NEW_CONTEXT_REQUIRED`
- `FAIL_CLOSED`

Allowed normal pairs are:

| Classification | Activation outcome | Meaning |
|---|---|---|
| `SAME_LOGICAL_INSTALLATION` | `PRESERVE_CONTEXT` | Continue the existing valid scope and secret generation. |
| `DISTINCT_LOGICAL_INSTALLATION` | `NEW_CONTEXT_REQUIRED` | Do not publish until a new scope and CA-001 secret generation exist at one atomic boundary. |
| `UNKNOWN` | `FAIL_CLOSED` | Publish no new identity-dependent current snapshot pending authorized resolution. |

When logical continuity is known but CA-001 state is unavailable or invalid, the
exception pair `SAME_LOGICAL_INSTALLATION` + `FAIL_CLOSED` SHALL be returned.
This preserves classification without bypassing CA-001 failure behavior. No
other pair is valid.

### 4.2 Deterministic decision algorithm

The evaluator SHALL apply D-001 through D-007 exactly once in order and stop at
the first matching rule:

| Rule | Condition | Exact result |
|---|---|---|
| D-001 | Existing CA-001 state or protected provenance is required by prior-existence evidence or a claimed transition and is missing, corrupt, unverifiable or internally contradictory | `UNKNOWN` + `FAIL_CLOSED` |
| D-002 | Positive validated evidence shows concurrent use of the same context outside a completed predecessor-retirement transition | `UNKNOWN` + `FAIL_CLOSED` |
| D-003 | Declaration is missing, unauthorized, stale, replayed, conflicting or inconsistent with provenance/supporting evidence | `UNKNOWN` + `FAIL_CLOSED` |
| D-004 | Valid `SEPARATION` declaration matches protected provenance | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| D-005 | Valid `CONTINUITY` declaration names exactly one predecessor, matches protected provenance and includes predecessor-retirement assertion | `SAME_LOGICAL_INSTALLATION` + `PRESERVE_CONTEXT` |
| D-006 | Valid first-creation provenance establishes no inherited identity state and no prior-existence marker | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| D-007 | No earlier condition matches | `UNKNOWN` + `FAIL_CLOSED` |

Supporting evidence MAY cause D-003 by contradiction. Supporting evidence MUST
NOT independently satisfy D-004, D-005 or D-006.

### 4.3 Scenario table

Every Batch 1A scenario is mapped below. “Required evidence” is in addition to
valid local CA-001 state unless the row concerns its failure. “Outcome” refers
to the first matching D-rule and is therefore single-valued for a concrete
evidence set.

| Scenario | Required evidence and authority | Deterministic outcome | Ambiguity gate | Fail-closed boundary |
|---|---|---|---|---|
| VM clone | Identity-authority declaration plus matching lineage; platform clone record only corroborates | D-004 for separation, D-005 only for completed continuity; otherwise D-002/D-003/D-007 | Missing intent, source retirement or possible concurrent VM | No new identity-dependent snapshot |
| LXC clone | Same as VM clone; container metadata is supporting only | D-004/D-005; otherwise `UNKNOWN` | Missing/stripped lineage or concurrent source | Same boundary |
| Snapshot restore | Declaration, snapshot lineage, generation continuity and predecessor/fork status | D-005 for continuity, D-004 for separation; rollback/fork conflict D-003 | Unknown active descendants or provenance rollback | Same boundary; CA-001 state failure also D-001 |
| Backup restore | Declaration, protected backup lineage and predecessor disposition | D-005 or D-004; repeated/conflicting restore D-002/D-003 | Backup reuse or source still active | Same boundary |
| Full disk restore | Declaration and lineage distinguishing restore from copied disk | D-005/D-004; absent provenance D-007 | Bitwise equality without operation intent | Same boundary |
| Hardware replacement | For complete-host change, continuity declaration, lineage and predecessor retirement | D-005 when complete; D-003/D-007 otherwise | Old host disposition unknown | Same boundary |
| Motherboard replacement | Uninterrupted protected lineage; board data is non-authoritative | Existing lineage remains D-005 only when a valid continuity declaration is already required by transition; board change alone cannot alter result | Identity-state transfer or lineage break | D-007 if transition classification becomes necessary and evidence is absent |
| CPU replacement | Uninterrupted valid context; CPU evidence ignored for identity | Existing classification is unchanged; if evaluated as a transition without declaration, D-007 | None from CPU itself | No automatic rotation; D-007 on attempted inference |
| NIC replacement | Uninterrupted valid context; NIC evidence ignored | Same as CPU replacement | None from NIC itself | Same |
| MAC-address change | Uninterrupted valid context; address ignored | Same as CPU replacement | None from MAC itself | Same |
| Hostname change | Uninterrupted valid context; hostname ignored | Same as CPU replacement | None from hostname itself | Same |
| OS reinstall | Declaration, prior-existence record and restored/new lineage | D-005 with exact continuity evidence; D-004 with separation declaration; missing state D-001/D-003 | “Clean” reinstall versus lost state | Same boundary |
| Fresh installation | Valid protected first-creation provenance and no prior-existence marker | D-006 | Any evidence of prior identity or missing provenance triggers D-001/D-003 | No publication until new context is atomically created under CA-001 |
| Image deployment | Declaration plus image/deployment lineage proving whether identity state was inherited | D-004 for intended new instance; D-005 only for one completed migration; otherwise D-003/D-007 | Embedded state or repeated deployment | Same boundary |
| Golden image deployment | Per-instance separation declaration and protected first-creation lineage; template attestation corroborates only | D-004/D-006 per instance; inherited template identity D-003 | Template contains identity state or provenance absent | Same boundary |
| Test environment copy | Separation declaration plus production/test lineage; environment label only supports | D-004; without it D-003/D-007 | Test designation or future connectivity uncertain | Same boundary |
| Production-to-test copy | Separation declaration and lineage binding source copy to distinct target | D-004; same-context activity D-002 | Source intentionally remains active | Same boundary |
| Concurrent cloned systems | Positive validated same-context concurrency evidence | D-002 regardless of prior continuity declaration until conflict is authoritatively resolved | Which environment, if any, is legitimate successor | All affected new identity-dependent publication fails closed |
| Air-gapped clone | Pre-activation declaration and protected lineage; lack of online conflict evidence has no weight | D-004/D-005 if authoritative evidence complete; otherwise D-003/D-007 | Unobservable active source | Same boundary |
| Secret loss | Existing lineage may establish logical continuity; CA-001 secret unavailable | `SAME_LOGICAL_INSTALLATION` + `FAIL_CLOSED` when continuity is already established; otherwise D-001 | Lineage also missing or loss versus unauthorized removal | CA-001 recovery only; no regeneration |
| Secret regeneration | Explicit separation/reset authority and generation provenance are required; unexplained generation is contradiction | D-004 only for authorized separation; otherwise D-001/D-003 | Legitimacy and predecessor lineage | No acceptance of regenerated secret under old context |
| Secret migration | Continuity declaration, exact protected transfer lineage and predecessor retirement | D-005; missing retirement D-003; concurrency D-002 | Copy versus move | Same boundary |
| Storage migration | Continuity declaration/lineage when duplicate storage can remain; path is ignored | D-005 when source disposition is established; otherwise D-003/D-007 | Original volume remains usable | Same boundary |
| Container migration | Continuity declaration, orchestrator evidence and predecessor retirement | D-005; split execution D-002; otherwise D-003 | Reschedule versus scale-out | Same boundary |
| Hypervisor migration | Continuity declaration, migration lineage and completed predecessor retirement | D-005; split-brain D-002; otherwise D-003 | Incomplete live migration | Same boundary |
| Unknown provenance | No sufficient authoritative declaration/lineage | D-001, D-003 or D-007 | Entire origin/intent is unresolved | `UNKNOWN` + `FAIL_CLOSED` |

## 5. Unknown-state handling

### 5.1 UNKNOWN classification

`UNKNOWN` SHALL be returned whenever exactly one authorized classification
cannot be proven under Section 4. It MUST NOT be converted to clone,
continuity, separation, fresh installation or migration by default.

### 5.2 Ambiguity gate

The ambiguity gate is entered by D-001, D-002, D-003 or D-007. While active:

- no new identity-dependent current snapshot SHALL be published;
- no scope or secret SHALL be generated, replaced, selected or rotated;
- no old/new identity SHALL be aliased;
- no declaration SHALL be synthesized from supporting evidence;
- a last valid immutable snapshot MAY remain only as explicitly stale;
- safe bounded diagnostics MAY expose the rule ID and evidence-class status but
  MUST NOT expose secrets, raw identifiers, private provenance or hardware
  fingerprints.

### 5.3 Required recovery path

Recovery SHALL require one of:

1. restoration/validation of missing protected provenance followed by reevaluation;
2. replacement of an invalid declaration by a current authorized declaration
   with matching protected provenance;
3. authoritative resolution of concurrent use, including predecessor/loser
   disposition, followed by reevaluation; or
4. a separately authorized separation/reset declaration leading through D-004.

Reevaluation SHALL restart at D-001. Recovery MUST NOT skip precedence rules.

### 5.4 Prohibited implementation behavior

Implementations MUST NOT resolve `UNKNOWN` through first-wins, last-wins,
traversal order, process restart, random choice, hardware/environment score,
automatic timeout, automatic secret regeneration or consumer preference.

## 6. Clone continuity

This section references CA-001; it does not redefine cryptographic derivation.

### 6.1 Preservation

`SAME_LOGICAL_INSTALLATION` + `PRESERVE_CONTEXT` SHALL preserve:

- installation scope bytes;
- CA-001 secret generation and exact secret bytes;
- CA-001 cryptographic format;
- public references for equal canonical inputs;
- observation identity where all frozen AI-001 observation-ID inputs remain equal;
- private collision registry and lineage required for that identity context.

Migration/restore provenance changes do not themselves enter CA-001 HMAC input
or frozen observation-ID input.

### 6.2 Discontinuity

`DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` SHALL require, before
publication and at one atomic snapshot boundary:

- a new installation scope generation;
- a new independent CA-001 secret generation;
- a new private collision-registry context;
- regenerated public references;
- regenerated observation identities whose installation-scope/reference inputs
  change.

Old and new identities MUST NOT be aliased, merged or represented as continuous.
Canonical-key grammar remains unchanged. Relationship `source_ref` consequences
remain reserved for C-003.

### 6.3 No automatic discontinuity

Hardware replacement, hostname/MAC/address change, restart, update, reload,
ordinary restore label or platform migration label MUST NOT alone trigger
discontinuity. Only D-004/D-006 can yield `NEW_CONTEXT_REQUIRED`.

## 7. Provenance

### 7.1 Required properties

Protected provenance SHALL be private, durable, append-preserving,
integrity-checked, atomically updated with the identity transition and available
before current-snapshot activation. Storage technology is not specified.

Missing, corrupt, unverifiable, forked or contradictory required provenance
triggers D-001 or D-003.

### 7.2 Minimum required information

Each transition record SHALL contain at least:

- provenance-format identifier;
- transition category: first creation, continuity, separation, restore,
  migration, replacement or recovery;
- declaration intent and identity-authority reference;
- predecessor lineage reference, or explicit none for validated first creation;
- predecessor-retirement assertion where continuity is declared;
- installation-scope generation reference without private raw scope source;
- CA-001 secret-generation reference that is not the secret or a digest of it;
- cryptographic-format reference;
- resulting classification and activation outcome;
- supporting-evidence references and validation result;
- concurrency-conflict status;
- immutable-snapshot boundary reference;
- previous provenance-record reference.

The identifiers above are private lineage references, not new public contract
fields and not identity derivation inputs.

### 7.3 Integrity and privacy

Provenance MUST:

- be protected by the producer's existing local administrative trust boundary;
- reject unauthorized modification, deletion, reordering and replay;
- retain sufficient predecessor history to evaluate all active/historical
  identity generations;
- remain outside public snapshots, reports, logs and consumer output;
- exclude secret bytes, secret digests, raw source identifiers, credentials,
  hostnames, addresses, MACs and hardware fingerprints;
- preserve discontinuity history without creating public aliases.

This specification defines required properties, not a database, file format,
signature scheme, path or API.

## 8. Platform evidence

Platform attestation MAY:

- corroborate that a copy, move, restore, image deployment or migration event
  occurred;
- identify that operation evidence conflicts with a declaration;
- supply a private supporting-evidence reference in provenance.

Platform attestation MUST NOT:

- independently establish `CONTINUITY`, `SEPARATION`, clone or freshness;
- override positive concurrency conflict or invalid provenance;
- enter scope, secret, reference or observation-ID derivation;
- require one vendor/platform for conformance;
- expose infrastructure identifiers publicly;
- be treated as authoritative merely because it is signed or machine-generated.

Unavailable platform evidence MUST NOT cause continuity or separation; the
remaining authoritative evidence is evaluated normally.

## 9. Concurrency

### 9.1 Positive evidence

Validated positive evidence of independently active same-context environments
SHALL trigger D-002. It overrides a continuity declaration until an authorized
resolution and consistent provenance are recorded.

### 9.2 Absent evidence

Lack of observed concurrency, lease conflict, network visibility or duplicate
publication MUST NOT prove uniqueness and MUST NOT satisfy D-004, D-005 or
D-006.

### 9.3 Offline and air-gapped systems

Offline or air-gapped operation SHALL use the same declaration/provenance rules.
Network coordination is not required. Absence of connectivity is neither clone
evidence nor uniqueness evidence. Incomplete declaration/provenance yields
D-003/D-007.

### 9.4 Split-brain

Positive split-brain evidence is concurrency evidence and SHALL trigger D-002.
No participant may self-elect by start time, uptime, hostname, address, hardware
identity, traversal order or first/last publication. Recovery follows Section
5.3.

## 10. Prohibited behavior

The following are prohibited:

- hardware-fingerprint identity or clone classification;
- hostname, IP, MAC, machine-ID, account, path or platform-ID identity;
- timestamp-only, boot-time or elapsed-time identity;
- random per-process/runtime identity;
- automatic secret regeneration after prior existence;
- automatic scope or secret rotation based only on copy/restore/platform labels;
- automatic clone inference without authoritative declaration/provenance;
- treating copied cryptographic state as proof of continuity;
- treating different hardware/environment as proof of separation;
- treating missing state as proof of freshness;
- treating absent concurrency evidence as proof of uniqueness;
- implementation-selected fallback, ordering or timeout semantics;
- public disclosure of declaration internals, private lineage, secret material or
  raw identity;
- changing CA-001 constants, canonical-key grammar, source-capability vocabulary,
  relationship predicates or active contract version under C-002.

## 11. Deterministic decision tables

### 11.1 Evidence-state decision table

Rows are evaluated top to bottom; the first match is final.

| Priority | Local/provenance state | Concurrency | Declaration | Lineage match | Exact result |
|---:|---|---|---|---|---|
| 1 | Required existing state is invalid/unavailable/contradictory | any | any | any | `UNKNOWN` + `FAIL_CLOSED` |
| 2 | Valid | positive same-context conflict | any | any | `UNKNOWN` + `FAIL_CLOSED` |
| 3 | Valid | no positive conflict | missing/invalid/conflicting/replayed/stale | any | `UNKNOWN` + `FAIL_CLOSED` |
| 4 | Valid | no positive conflict | valid `SEPARATION` | yes | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| 5 | Valid | no positive conflict | valid `CONTINUITY` with one predecessor-retirement assertion | yes | `SAME_LOGICAL_INSTALLATION` + `PRESERVE_CONTEXT` |
| 6 | Valid first-creation state | no positive conflict | valid first-creation authority | no predecessor and no prior marker | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| 7 | Valid | no positive conflict | any other state | any | `UNKNOWN` + `FAIL_CLOSED` |

### 11.2 Transition table

| Transition/evidence state | Scope | Secret generation | References/observation identity | Exact outcome |
|---|---|---|---|---|
| Valid continuity | preserve | preserve | preserve when canonical inputs equal | `SAME_LOGICAL_INSTALLATION` + `PRESERVE_CONTEXT` |
| Valid separation | new generation required | new generation required | regenerate; no alias | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| Valid first creation | create new | create new | create under new context | `DISTINCT_LOGICAL_INSTALLATION` + `NEW_CONTEXT_REQUIRED` |
| Unknown/contradictory provenance | unchanged while blocked | unchanged while blocked | emit none new | `UNKNOWN` + `FAIL_CLOSED` |
| Positive concurrent clone | unchanged while blocked | unchanged while blocked | emit none new | `UNKNOWN` + `FAIL_CLOSED` |
| Known continuity with secret unavailable | preserve intended context; unavailable | preserve; recover exact bytes | emit none new; last valid may remain stale | `SAME_LOGICAL_INSTALLATION` + `FAIL_CLOSED` |
| Unauthorized secret regeneration | do not select/replace | reject unexplained generation | emit none new | `UNKNOWN` + `FAIL_CLOSED` |
| Hardware/environment-only change with uninterrupted valid context | preserve | preserve | preserve | existing `SAME_LOGICAL_INSTALLATION` + `PRESERVE_CONTEXT` |

No transition state outside these rows is valid; unmatched evidence uses D-007.

### 11.3 Scenario coverage index

| Scenario group | Covered scenarios | Governing rules |
|---|---|---|
| Virtual copies | VM clone, LXC clone, image deployment, golden image, test copy, production-to-test copy | D-002 through D-007 |
| Restore/recovery | snapshot restore, backup restore, full disk restore, OS reinstall | D-001 through D-007 |
| Host/component changes | hardware, motherboard, CPU, NIC, MAC, hostname | D-003, D-005, D-007; prohibited-evidence rules |
| Migration | secret, storage, container, hypervisor migration | D-002, D-003, D-005 |
| Concurrency | concurrent clone, air-gapped clone, split-brain | D-002, D-003, D-007 |
| Secret state | loss, regeneration, migration | D-001 through D-005 plus CA-001 |
| Origin state | fresh installation, unknown provenance | D-001, D-003, D-006, D-007 |

## 12. Traceability

### 12.1 Rule-group traceability

| Normative rule group | DF-002 | AI-001 | R-003 | Accepted CA-001/R-004 | Clone Decision Record |
|---|---|---|---|---|---|
| Logical installation is not host/environment identity | Installation-scoped privacy | Logical identity domain | F-002 rejects undefined intent | Host/address/machine data excluded from derivation | Reject environmental fingerprint |
| Declaration plus lineage authority model | Determinism/no inference | Intended same/new distinction | Requires authoritative classification | Copy classification explicitly deferred | Core A+B recommendation |
| Supporting/platform evidence cannot decide alone | Portable deterministic model | Host-independent identity | Prevent implementation choice | Cryptographic equality does not establish intent | C corroborative only |
| Positive concurrency contradiction; absence proves nothing | Cross-installation non-correlation | Concurrent clone risk | Requires concurrent-clone behavior | Same secret/scope reproduces references | D cannot stand alone |
| UNKNOWN ambiguity gate | Fail-closed unsafe capability | Missing/corrupt state blocks | Requires safe unknown outcome | Secret/collision failures fail closed | E accepted component |
| Continuity preserves scope/secret | Stable authorized joins | Preserve intended continuity | Requires exact clone transition | Exact restore preserves derivation | A+B core |
| Separation changes scope/secret | Cross-installation separation | New installation changes IDs | Requires rotation semantics | Secret/scope change identity-affecting | Reject always-preserve |
| No automatic restore/hardware rotation | Stability | Host-independent continuity | Avoid nondeterministic classification | Ordinary restore and host changes are not auto-rotation triggers | Reject always-rotate/fingerprint |
| Protected private provenance | Secret/raw mapping excluded | Persistent scope history | Requires authoritative evidence/audit | Private generation/collision provenance | B accepted component |
| Complete scenario/decision tables | Deterministic consumer contract | Stability matrix base | F-002 closure test | Atomic snapshot/fail-closed boundaries | Combination rationale |

### 12.2 Batch 1A ambiguity closure

| Batch 1A ambiguity | Normative handling |
|---|---|
| Copy versus move | D-005 requires declaration, lineage and predecessor retirement; otherwise `UNKNOWN`. |
| Restore versus fork | Declaration/lineage plus concurrency precedence; unresolved descendants yield `UNKNOWN`. |
| Same versus new logical installation | Only D-004/D-005/D-006 classify; environment cannot. |
| Local validity versus global uniqueness | Positive concurrency blocks; absent evidence proves nothing. |
| Migration versus unauthorized copy | Identity authority plus provenance required. |
| Missing versus intentionally fresh | D-006 requires first-creation provenance; absence alone reaches D-001/D-007. |
| Environment drift versus identity transition | Environment evidence prohibited as independent authority. |
| Concurrent duplicate detection | D-002 for positive evidence; absence has no effect. |
| Secret versus installation rotation | Continuity preserves both; separation creates both; other combinations fail/are out of C-002. |
| Historical continuity after separation | No aliasing; private lineage preserves discontinuity only. |

### 12.3 Decision-record recommendation consumption

- Strategy A is consumed as authoritative declaration.
- Strategy B is consumed as protected provenance.
- Strategy E is consumed as the `UNKNOWN` ambiguity gate.
- Strategy C is consumed only as supporting platform attestation.
- Strategy D is consumed only as positive concurrency evidence; it cannot prove
  uniqueness.
- Strategies F, G and H are normatively prohibited as classification policies.

## Validation conclusion

- Batch 1A scenarios covered: 26 of 26.
- Decision Record recommendations consumed: 8 of 8 strategy dispositions.
- Batch 1A ambiguities deterministically handled: 10 of 10.
- Undefined classification states: 0; D-007 is the closed fallback.
- CA-001 cryptographic rules changed: 0.
- Implementation/storage details introduced: 0.
- Governance changes: 0.
- Contract changes: 0.

**CLONE_IDENTITY_SPECIFICATION_COMPLETE_FOR_AI002_REVIEW_PACKAGE**
