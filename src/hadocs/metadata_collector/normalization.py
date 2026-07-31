"""Deterministic normalization without interpretation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contract import Observation, Relationship, Snapshot
from .errors import RegistrationError
from .registry import ContractRegistry


def canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): canonical_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    return value


class Normalizer:
    def __init__(self, registry: ContractRegistry | None = None) -> None:
        self.registry = registry or ContractRegistry()

    def normalize(self, snapshot: Snapshot) -> Snapshot:
        for item in snapshot.observations:
            self.registry.validate_observation_category(item.category)
        for item in snapshot.relationships:
            self.registry.validate_relationship_predicate(item.predicate)

        observations = self._unique(
            snapshot.observations, lambda item: item.observation_id, "duplicate_observation"
        )
        relationships = self._unique(
            snapshot.relationships, lambda item: item.relationship_id, "duplicate_relationship"
        )
        capabilities = self._unique(
            snapshot.capabilities, lambda item: item.capability_id, "duplicate_capability_status"
        )
        return Snapshot(
            snapshot_id=snapshot.snapshot_id,
            observed_at=snapshot.observed_at,
            producer=snapshot.producer,
            source=snapshot.source,
            capabilities=tuple(sorted(capabilities, key=lambda item: item.capability_id)),
            observations=tuple(sorted(observations, key=lambda item: item.observation_id)),
            relationships=tuple(sorted(relationships, key=lambda item: item.relationship_id)),
        )

    @staticmethod
    def _unique(items, identity, code):
        result = {}
        for item in items:
            key = identity(item)
            if key in result and result[key] != item:
                raise RegistrationError(code)
            result[key] = item
        return tuple(result.values())

