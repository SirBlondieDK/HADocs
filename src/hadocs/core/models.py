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


# Backwards-compatible alias while the rest of HADocs migrates.
HADocsModel = InstallationModel
