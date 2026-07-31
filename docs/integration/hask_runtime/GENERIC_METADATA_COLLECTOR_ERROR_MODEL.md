# Generic Metadata Collector Error Model

## Safe error taxonomy

| Condition | Capability status | Required behavior |
|---|---|---|
| Documented capability absent | `unsupported` | Continue; do not infer HA health or version defect. |
| Permission denied | `permission_denied` | Continue; do not expose user/permission details. |
| API unavailable | `unavailable` | Bounded retry if safe; preserve no invented observations. |
| Unsupported source evolution | `invalid_response` | Reject affected payload; retain other capabilities. |
| Authentication expired | `authentication_expired` | Do not retry with or expose credentials. |
| Partial payload | `partial` | Export only independently valid observations and identify incomplete scope. |
| Unknown field | unchanged or `partial` by policy | Ignore field; never pass through. |

## Error envelope

The public capability record may contain only a stable safe code, retryability flag and status timestamp. Raw exception types, stack traces, URLs, payload fragments and server messages remain internal and must be sanitized before any operational log.

## Retry policy

Retries apply only to idempotent documented read operations, use a bounded attempt count with backoff, and stop on permission, authentication, unsupported or schema errors. Exact timing is an implementation configuration, not part of the public contract. A retry never changes the meaning of a source response.

## Partial collection

A snapshot may be published when at least its envelope and capability statuses are valid. Observations from a failed capability are absent and that absence has no semantic meaning. A previous snapshot may be served only as explicitly stale data; it must never be merged invisibly with current observations.

