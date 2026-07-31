# R-003 Stability Review

Repeated collection, source reordering, restarts, reloads, compatible updates, backup/restore with scope, replacement-host restore and explicit migration deterministically preserve IDs. Canonical input or scope replacement changes IDs. Corrupt/unavailable scope prevents new identity publication. Recreation with the same source ID preserves identity; a new source ID changes it.

Defects:

- Clone results require an undefined intention/declaration mechanism.
- Component, event and entity removal is `IDENTITY_INVALID` in the matrix but absence-only elsewhere. Removal does not make the stable identity algorithm invalid; it produces no current observation. Implementations cannot choose between invalid capability handling and ordinary absence.

All required events are covered syntactically, but not with consistent supported semantics.

Stability gate: **FAIL**.

