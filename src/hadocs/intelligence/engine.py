from __future__ import annotations

from src.hadocs.core.models import EntityModel
from src.hadocs.intelligence.profiles import (
    ACTION_PROFILE,
    AVAILABILITY_PROFILE,
    CONFIGURATION_PROFILE,
    CONTROL_PROFILE,
    DIAGNOSTIC_PROFILE,
    EVENT_PROFILE,
    MEASUREMENT_PROFILE,
    UNKNOWN_PROFILE,
    EntityProfile,
)
from src.hadocs.utils.normalize import normalize_text


_ACTION_DOMAINS = {
    "button",
    "scene",
    "notify",
}

_EVENT_DOMAINS = {
    "event",
}

_CONTROL_DOMAINS = {
    "switch",
    "light",
    "lock",
    "cover",
    "climate",
    "fan",
    "siren",
    "valve",
    "water_heater",
    "vacuum",
    "lawn_mower",
}

_CONFIGURATION_DOMAINS = {
    "number",
    "select",
    "text",
    "input_boolean",
    "input_number",
    "input_select",
    "input_text",
}

_AVAILABILITY_DEVICE_CLASSES = {
    "connectivity",
    "problem",
    "running",
}

_EVENT_DEVICE_CLASSES = {
    "motion",
    "occupancy",
    "presence",
    "sound",
    "tamper",
    "vibration",
    "opening",
    "door",
    "window",
    "garage_door",
}

_AVAILABILITY_ID_PARTS = (
    "availability",
    "available",
    "connection_state",
    "connectivity",
    "connected",
    "device_status",
    "node_status",
    "online",
    "reachable",
    "reachability",
)

_EXPECTED_ACTION_SUFFIXES = (
    "_ping",
    "_battery_replaced",
    "_identify",
    "_restart",
    "_reboot",
)


def _state_attributes(entity: EntityModel) -> dict:
    attributes = getattr(entity, "attributes", None)
    if isinstance(attributes, dict):
        return attributes

    state_raw = getattr(entity, "state_raw", None)
    if isinstance(state_raw, dict):
        raw_attributes = state_raw.get("attributes")
        if isinstance(raw_attributes, dict):
            return raw_attributes

    return {}


def _registry_metadata(entity: EntityModel) -> dict:
    registry = getattr(entity, "registry", None)
    if isinstance(registry, dict):
        return registry

    return {}


def _raw_metadata(entity: EntityModel) -> dict:
    raw = getattr(entity, "raw", None)
    if isinstance(raw, dict):
        return raw

    return {}


def profile_entity(entity: EntityModel) -> EntityProfile:
    """Classify a Home Assistant entity by semantics rather than raw state."""

    entity_id = normalize_text(entity.entity_id)
    domain = normalize_text(entity.domain)
    importance = normalize_text(entity.importance)

    attributes = _state_attributes(entity)
    registry = _registry_metadata(entity)
    raw = _raw_metadata(entity)

    entity_category = normalize_text(
        registry.get("entity_category")
        or attributes.get("entity_category")
        or raw.get("entity_category")
    )
    device_class = normalize_text(
        attributes.get("device_class")
        or registry.get("device_class")
        or registry.get("original_device_class")
        or raw.get("device_class")
        or raw.get("original_device_class")
    )

    if entity.is_ignored:
        return DIAGNOSTIC_PROFILE

    if normalize_text(
        registry.get("disabled_by")
        or raw.get("disabled_by")
    ):
        return DIAGNOSTIC_PROFILE

    if importance in {"diagnostic", "ignored"}:
        return DIAGNOSTIC_PROFILE

    if entity_category == "diagnostic":
        return DIAGNOSTIC_PROFILE

    if entity_category == "config":
        return CONFIGURATION_PROFILE

    if domain in _ACTION_DOMAINS:
        return ACTION_PROFILE

    if domain in _EVENT_DOMAINS:
        return EVENT_PROFILE

    if domain == "update":
        return DIAGNOSTIC_PROFILE

    if entity_id.endswith(_EXPECTED_ACTION_SUFFIXES):
        return ACTION_PROFILE

    if any(part in entity_id for part in _AVAILABILITY_ID_PARTS):
        return AVAILABILITY_PROFILE

    if device_class in _AVAILABILITY_DEVICE_CLASSES:
        return AVAILABILITY_PROFILE

    if (
        domain == "binary_sensor"
        and device_class in _EVENT_DEVICE_CLASSES
    ):
        return EVENT_PROFILE

    if domain == "sensor":
        return MEASUREMENT_PROFILE

    if domain == "binary_sensor":
        return MEASUREMENT_PROFILE

    if domain in _CONTROL_DOMAINS:
        return CONTROL_PROFILE

    if domain in _CONFIGURATION_DOMAINS:
        return CONFIGURATION_PROFILE

    return UNKNOWN_PROFILE