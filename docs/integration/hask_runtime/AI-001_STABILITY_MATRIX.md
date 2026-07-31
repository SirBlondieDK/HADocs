# AI-001 Identity Stability Matrix

Codes: `MUST_REMAIN`, `MUST_CHANGE`, `MAY_CHANGE`, `IDENTITY_INVALID`.

Unless a category-specific source identity changes, all four categories share these rules:

| Event | API | Component | Event type | Entity |
|---|---|---|---|---|
| repeated/reordered collection | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| process, collector, HA or host restart | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| configuration reload | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| compatible patch/minor update | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| backup/restore same installation | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| restore to replacement host with scope | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| explicit migration with scope | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| clone retained as same logical installation | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| clone declared new installation | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |
| source-object display rename only | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| source identity rename/change | MUST_REMAIN | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |
| source removal | MUST_REMAIN | IDENTITY_INVALID | IDENTITY_INVALID | IDENTITY_INVALID |
| recreation with same source ID | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN | MUST_REMAIN |
| recreation with new source ID | MUST_REMAIN | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |
| category change | IDENTITY_INVALID | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |
| canonical-key input change | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |
| installation-scope corruption | IDENTITY_INVALID | IDENTITY_INVALID | IDENTITY_INVALID | IDENTITY_INVALID |
| installation-scope replacement | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE | MUST_CHANGE |

API identity has a fixed source object and therefore does not change for ordinary object rename/removal cases; an unavailable endpoint yields no current observation, not a renamed identity. `MAY_CHANGE` is unused because every listed event has a normative result. A compatible update must preserve identity format 1; a future approved identity-format change defines its own migration and version boundary.

