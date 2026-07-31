# I-001A Generic Metadata Collector Infrastructure — Implementation Report

## Result

The infrastructure defined by DF-001 has been implemented as the isolated `hadocs.metadata_collector` package. It is disabled by default, imports no Home Assistant provider, registers no capability and is not connected to scanning, runtime, HASK, Consumer Contract or PI2.

## Implemented infrastructure

- Frozen contract identity and immutable contract value objects.
- Closed observation-category and relationship-predicate registries.
- Empty injectable capability registry and future extension point.
- Deterministic normalization and canonical UTF-8 JSON serialization.
- Fail-closed privacy transformer with no default sensitive-reference algorithm.
- Contract 1.x negotiation and contract registration.
- Disabled-by-default lifecycle, immutable snapshot activation and deactivation.
- Configuration and passive refresh-scheduling policy holder.
- Safe exception taxonomy and injectable standard-library logger.
- Dependency-injected bootstrap and implementation metadata.

## Explicit non-implementation

No REST or WebSocket client, Home Assistant call, Release 1 capability, metadata collection, observation production, relationship production, diagnostics, matcher, score, recommendation, HASK adapter or runtime hook was implemented. The snapshot executor refuses to run registered capabilities under I-001A and can exercise only an empty infrastructure snapshot supplied with caller-owned execution metadata.

## Baseline test result

The existing suite collected 251 tests: 239 passed and 12 pre-existing GUI/import tests failed because the available Python 3.14 project-local validation environment lacks the unrelated `requests` dependency. Existing HASK pilot and runtime tests passed. Dependencies were not changed because I-001A does not authorize dependency updates.

## Conclusion

The infrastructure conforms to frozen contract 1.0.0. Release 1 collection remains not started.

