# AI-001 Versioning Recommendation

Recommendation: retain `hadocs-generic-metadata` 1.0.0 if R-003 approves and DF-003 freezes this proposal.

The identity fields existed but had no complete normative observable values. No Release 1 producer emitted production identities, V-001 has not verified output, and no consumer adopted it. AI-001 fixes the initial bytes before the first operational producer contract rather than changing deployed 1.x behavior.

The proposal makes serialization newly deterministic and therefore becomes binding from the first release. After producer release or consumer adoption, changing `ck1`, `is1`, `ref1`, `obs1`, `rel1`, input ordering, framing, domains or capability vocabulary would have version consequences under the existing strategy—normally major when existing identities change.

AI-001 does not change or approve the version. R-003 must decide; DF-003 must record it. Migration from I-001A requires none because I-001A emitted no Release 1 observations.

