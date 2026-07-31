# G-001 Implementation Rules

Every implementation increment shall:

- identify and reference the active Design Freeze;
- inventory its authorized frozen scope before changing code;
- preserve contract names, versions, identities, fields, relationships and semantics;
- implement no capability or observation absent from the frozen baseline;
- preserve privacy, read-only, lifecycle, normalization and version guarantees;
- keep operational defaults within frozen boundaries;
- separate pre-existing failures and changes from increment results;
- produce implementation evidence traceable to the freeze;
- complete verification before consumer adoption.

An implementation increment shall not redefine architecture through code structure, defaults, error handling, tests, fixtures or undocumented behavior. Passing tests cannot authorize behavior that the frozen contract does not define.

Under the current baseline, future Generic Metadata Collector implementation references DF-002. G-001 itself authorizes no implementation.

