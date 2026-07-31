# DF-002 Change Control

All future Generic Metadata Collector implementation increments shall reference DF-002.

Implementation may realize only the four frozen Release 1 capabilities, four observation categories and four relationship predicates. It may choose mechanisms and operational defaults only within the frozen contract, privacy, lifecycle and version guarantees.

Any architectural modification requires all of:

1. A demonstrated Architecture Defect.
2. An approved Architecture Increment.
3. An Architecture Review.
4. A new Design Freeze superseding DF-002 for the affected scope.

Implementation convenience, stylistic preference or speculative expansion is insufficient justification. A future increment may not reintroduce `websocket_feature` or `supported_features` as metadata without completing this governance path.

DF-001 remains immutable governance history. A-001 and R-002 provide traceability for the sole amendment incorporated by DF-002.

