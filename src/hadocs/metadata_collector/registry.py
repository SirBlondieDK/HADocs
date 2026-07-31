"""Closed contract registries and an empty future capability registry."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from .errors import RegistrationError

APPROVED_OBSERVATION_CATEGORIES = (
    "api_availability",
    "entity_display_reference",
    "loaded_component",
    "registered_event_type",
    "websocket_feature",
)

APPROVED_RELATIONSHIP_PREDICATES = (
    "entity_assigned_to_area",
    "entity_assigned_to_device",
    "entity_has_label",
    "entity_uses_platform",
)


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str
    execute: Callable[..., object]


class ContractRegistry:
    """Read-only registry of the names frozen by DF-001."""

    @property
    def observation_categories(self) -> tuple[str, ...]:
        return APPROVED_OBSERVATION_CATEGORIES

    @property
    def relationship_predicates(self) -> tuple[str, ...]:
        return APPROVED_RELATIONSHIP_PREDICATES

    def validate_observation_category(self, category: str) -> None:
        if category not in APPROVED_OBSERVATION_CATEGORIES:
            raise RegistrationError("unknown_observation_category")

    def validate_relationship_predicate(self, predicate: str) -> None:
        if predicate not in APPROVED_RELATIONSHIP_PREDICATES:
            raise RegistrationError("unknown_relationship_predicate")


class CapabilityRegistry:
    """Infrastructure extension point; I-001A registers no capabilities."""

    def __init__(self) -> None:
        self._items: dict[str, CapabilityDefinition] = {}

    def register(self, definition: CapabilityDefinition) -> None:
        if not definition.capability_id or definition.capability_id in self._items:
            raise RegistrationError("duplicate_or_empty_capability")
        self._items[definition.capability_id] = definition

    def get(self, capability_id: str) -> CapabilityDefinition:
        try:
            return self._items[capability_id]
        except KeyError as exc:
            raise RegistrationError("unknown_capability") from exc

    @property
    def items(self) -> Mapping[str, CapabilityDefinition]:
        return MappingProxyType(dict(sorted(self._items.items())))

    @property
    def size(self) -> int:
        return len(self._items)

