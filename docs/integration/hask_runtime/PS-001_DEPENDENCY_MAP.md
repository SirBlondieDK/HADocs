# PS-001 Dependency Map

## Governance lifecycle

```text
Discovery -> Specification -> Review -> Design Freeze
          -> Implementation -> Verification -> Consumer Adoption
```

Ambiguity during implementation returns through Architecture Defect, Architecture Increment, Review and a new Design Freeze before implementation resumes.

## Actual program chain

```text
D-001 -> S-001 -> R-001 -> DF-001 -> I-001A
                                      |
                                      +-> I-001B attempt -> A-001 -> R-002 -> DF-002
                                                                        |
                                               G-001 governs -----------+
                                                                        v
                                                         I-001B resume -> V-001
                                                                          |
                                                             verification gate
                                                                          v
                                                                        K-001
                                                                          |
                                                          consumer-adoption gate
                                                                          v
                                                                        PI-001
```

## Relationship types

- Historical sequence: D-001 through G-001 records how the current baseline arose.
- Active authority: G-001 governs; DF-002 defines implementation.
- Execution dependency: I-001B resume requires both G-001 and DF-002.
- Verification gate: V-001 requires completed I-001B.
- Consumer gate: K-001 and downstream adoption require successful V-001.
- Historical preservation: DF-001 remains complete but is no longer the implementation baseline.

PS-001 records navigation only and grants no approval.

