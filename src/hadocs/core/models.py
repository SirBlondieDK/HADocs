from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EntityModel:
    entity_id: str
    name: str
    domain: str
    platform: str
    state: str
    area_id: str | None
    device_id: str | None
    is_ignored: bool
    is_physical: bool
    importance: str = "normal"
    rule_reason: str = ""

    # Current Home Assistant state context.
    attributes: dict[str, Any] = field(default_factory=dict)
    last_changed: str | None = None
    last_updated: str | None = None
    last_reported: str | None = None

    # Entity Registry metadata and complete state payload.
    registry: dict[str, Any] = field(default_factory=dict)
    state_raw: dict[str, Any] = field(default_factory=dict)

    # Backwards-compatible registry data.
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DeviceModel:
    device_id: str
    name: str
    area_id: str | None
    manufacturer: str
    model: str
    sw_version: str
    hw_version: str
    classification: str
    entities: list[EntityModel] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_physical(self) -> bool:
        return self.classification == "physical"

    @property
    def is_system(self) -> bool:
        return self.classification == "system"

    @property
    def is_virtual(self) -> bool:
        return self.classification == "virtual"


@dataclass(slots=True)
class AreaModel:
    area_id: str
    name: str
    entities: list[EntityModel] = field(default_factory=list)
    devices: list[DeviceModel] = field(default_factory=list)


@dataclass(slots=True)
class IntegrationModel:
    platform: str
    entities: list[EntityModel] = field(default_factory=list)
    devices: list[DeviceModel] = field(default_factory=list)


@dataclass(slots=True)
class DeviceHealth:
    device: DeviceModel
    status: str
    score: int
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InstallationModel:
    areas: dict[str, AreaModel]
    devices: dict[str, DeviceModel]
    entities: dict[str, EntityModel]
    integrations: dict[str, IntegrationModel]
    config: dict[str, Any]
    states: list[dict[str, Any]]
    services: list[dict[str, Any]]
    labels: list[dict[str, Any]]
    raw: dict[str, Any]

    def get_area(self, area_id: str) -> AreaModel | None:
        return self.areas.get(area_id)

    def get_device(self, device_id: str) -> DeviceModel | None:
        return self.devices.get(device_id)

    def get_entity(self, entity_id: str) -> EntityModel | None:
        return self.entities.get(entity_id)

    def get_integration(self, platform: str) -> IntegrationModel | None:
        return self.integrations.get(platform)

    def area_for_entity(self, entity_id: str) -> AreaModel | None:
        """Return the area assigned to an entity, if available."""
        entity = self.get_entity(entity_id)
        if entity is None or not entity.area_id:
            return None

        return self.get_area(entity.area_id)

    def device_for_entity(self, entity_id: str) -> DeviceModel | None:
        """Return the device assigned to an entity, if available."""
        entity = self.get_entity(entity_id)
        if entity is None or not entity.device_id:
            return None

        return self.get_device(entity.device_id)

    def entities_for_platform(self, platform: str) -> list[EntityModel]:
        """Return all entities belonging to an integration platform."""
        integration = self.get_integration(platform)
        if integration is None:
            return []

        return list(integration.entities)

    def unavailable_entities(self) -> list[EntityModel]:
        """Return entities whose current state is unavailable."""
        return [
            entity
            for entity in self.entities.values()
            if entity.state == "unavailable"
        ]

    def unknown_entities(self) -> list[EntityModel]:
        """Return entities whose current state is unknown."""
        return [
            entity
            for entity in self.entities.values()
            if entity.state == "unknown"
        ]

    def physical_devices(self) -> list[DeviceModel]:
        """Return all devices classified as physical."""
        return [
            device
            for device in self.devices.values()
            if device.is_physical
        ]


# Backwards-compatible alias while the rest of HADocs migrates.
HADocsModel = InstallationModel
