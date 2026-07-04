from dataclasses import dataclass, field
from typing import Any


@dataclass
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


@dataclass
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


@dataclass
class AreaModel:
    area_id: str
    name: str
    entities: list[EntityModel] = field(default_factory=list)
    devices: list[DeviceModel] = field(default_factory=list)


@dataclass
class IntegrationModel:
    platform: str
    entities: list[EntityModel] = field(default_factory=list)
    devices: list[DeviceModel] = field(default_factory=list)


@dataclass
class DeviceHealth:
    device: DeviceModel
    status: str
    score: int
    reasons: list[str] = field(default_factory=list)


@dataclass
class HADocsModel:
    areas: dict[str, AreaModel]
    devices: dict[str, DeviceModel]
    entities: dict[str, EntityModel]
    integrations: dict[str, IntegrationModel]
    raw: dict[str, Any]
