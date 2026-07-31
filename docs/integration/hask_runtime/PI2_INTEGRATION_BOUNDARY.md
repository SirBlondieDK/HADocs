# PI2 Integration Boundary

## Finding

The least invasive conceptual boundary is after native collection/model construction and before report/API serialization. A single optional enrichment service could consume finalized native observations and a validated immutable PI1 snapshot without changing native scoring or result semantics.

That service cannot be connected safely in the current system because the required native observation does not exist.

## Current native inputs

`InstallationCollector` collects only:

- states
- configuration metadata
- services
- entity registry
- device registry
- area registry
- labels

`build_model` converts those values into entities, devices, areas, integrations, and raw snapshot data. The integration model groups entities and devices by platform. It does not contain config-entry lifecycle, setup exceptions, coordinator failures, controller reachability, or API-session results.

## Existing observation semantics

HADocs can observe entity states such as `unavailable` and can calculate aggregate integration health. Neither is equivalent to a failed UniFi controller connection or failed MikroTik API connection:

- entity unavailability can have multiple causes and must not be promoted to a root cause or connection failure;
- aggregate integration health is derived from device/entity state and is a score/status, not a transport result;
- a generic connectivity binary sensor may describe an individual device rather than the integration controller or API session;
- platform identity alone provides no positive failure evidence.

Therefore none can truthfully produce the required structured fields `observation_type=connectivity_result`, `connection_result=failed`, and `problem_signal=true`.

## Candidate, recommendation, report, and API boundaries

Additive namespaced output remains architecturally feasible after a genuine structured observation exists. Candidate-only causes, advisory recommendations, verification guidance, and preservation outcomes can then be attached without modifying native results. No report or API breaking change was identified during this review.

## Disabled behavior

An isolated optional service can preserve existing behavior when disabled. This design was not implemented because its input contract would currently be empty or would require prohibited inference.

