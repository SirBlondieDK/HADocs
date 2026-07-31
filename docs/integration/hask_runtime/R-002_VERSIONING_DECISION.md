# R-002 Versioning Decision

Decision: retain `hadocs-generic-metadata` 1.0.0 for the corrected producer contract candidate.

## Existing strategy applied

The frozen strategy assigns major-version consequences to removal from a public producer contract. In this case no Release 1 producer implementation completed, no contract artifact was operationally released, and no HASK, Consumer Contract or PI2 consumer adopted `websocket_feature`. The candidate has therefore never produced the removed public semantic.

R-002 corrects the pre-implementation candidate before its first operational producer release. Contract 1.0.0 remains the initial producer contract rather than a backward-incompatible successor to a deployed 1.x contract. This does not create a general exception for released contracts: after production, removal or reinterpretation remains a major change under the unchanged strategy.

## Recorded result

Revised Collector Contract Version: `1.0.0`

The version strategy itself is unchanged.

