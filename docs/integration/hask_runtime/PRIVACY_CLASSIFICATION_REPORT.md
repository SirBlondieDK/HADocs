# Privacy Classification Report

- `PUBLIC`: protocol feature flags, pong envelopes and non-identifying schema metadata; preserve.
- `LOCAL_ONLY`: component/event/service identifiers and counts; preserve when needed, avoid installation fingerprints in shared reports.
- `SENSITIVE`: entity/device/area IDs and names, state attributes, history, logbook, calendars, locations, filesystem paths, URLs and diagnostics; anonymize or omit through allowlists.
- `SECRET`: tokens, signed URLs, cookies, webhook material, certificates and authentication grants; never collect or persist.

Device connections, identifiers, serials and configuration URLs must be removed rather than blocklist-scrubbed. Free log text, camera images, calendar event content and caller-rendered templates are excluded. Stable local IDs may be deterministically hashed only when graph continuity is necessary and the salt remains local.

