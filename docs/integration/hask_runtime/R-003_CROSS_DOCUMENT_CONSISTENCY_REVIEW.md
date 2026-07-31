# R-003 Cross-Document Consistency Review

The key grammar, source-capability vocabulary, byte framing, observation-ID vectors and scope token are consistent across AI-001 documents.

Material inconsistency:

- `AI-001_STABILITY_MATRIX.md` maps source removal to `IDENTITY_INVALID` for component, event and entity categories.
- `AI-001_ARCHITECTURE_PROPOSAL.md` and `AI-001_CATEGORY_IDENTITY_PROFILES.md` say removal is absence from the current snapshot and does not invalidate or assert failure.

The privacy analysis also calls the public-scope keyed references acceptable under the frozen privacy model, while that model requires non-reversibility without secret local material. That is a compatibility conflict rather than mere wording.

Cross-document consistency gate: **FAIL**.

