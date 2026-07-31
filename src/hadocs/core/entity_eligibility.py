from __future__ import annotations

from collections.abc import Mapping
from typing import Any


DOCUMENTED_REGISTRY_DISABLED_BY = frozenset({"user", "integration"})


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _normalized_disabled_by(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip().casefold()
        return normalized or None
    return "unknown"


def registry_disabled_by(entity: Any) -> str | None:
    """Return a safe normalized registry-disabled marker, when present.

    Home Assistant documents ``user`` and ``integration`` for the affected
    product paths. Unknown non-null markers remain disabled fail-closed rather
    than becoming active analytical evidence.
    """

    direct = _normalized_disabled_by(_get(entity, "disabled_by"))
    if direct is not None:
        return direct

    for container_name in ("registry", "entity_registry", "raw"):
        container = _get(entity, container_name, {})
        if not isinstance(container, Mapping):
            continue
        marker = _normalized_disabled_by(container.get("disabled_by"))
        if marker is not None:
            return marker
    return None


def is_registry_disabled_entity(entity: Any) -> bool:
    marker = registry_disabled_by(entity)
    if marker in DOCUMENTED_REGISTRY_DISABLED_BY:
        return True
    return marker is not None


def is_disabled_entity(entity: Any) -> bool:
    """Return whether an entity is excluded from active analytical surfaces."""

    if is_registry_disabled_entity(entity):
        return True
    if bool(_get(entity, "disabled", False)):
        return True
    state = str(_get(entity, "state", "")).strip().casefold()
    return state in {"disabled", "unavailable_disabled"}
