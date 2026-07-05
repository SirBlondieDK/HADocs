from dataclasses import dataclass, field

from src.hadocs.core.models import HADocsModel, DeviceModel, EntityModel, IntegrationModel


@dataclass
class EntityRelationship:
    entity_id: str
    name: str
    domain: str
    state: str
    area_id: str | None
    device_id: str | None
    device_name: str
    integration: str
    importance: str
    is_ignored: bool


@dataclass
class DeviceRelationship:
    device_id: str
    name: str
    area_id: str | None
    classification: str
    integrations: list[str] = field(default_factory=list)
    important_entities: list[str] = field(default_factory=list)
    diagnostic_entities: list[str] = field(default_factory=list)
    ignored_entities: list[str] = field(default_factory=list)
    problem_entities: list[str] = field(default_factory=list)


@dataclass
class IntegrationRelationship:
    platform: str
    devices: list[str] = field(default_factory=list)
    important_entities: list[str] = field(default_factory=list)
    diagnostic_entities: list[str] = field(default_factory=list)
    ignored_entities: list[str] = field(default_factory=list)
    problem_entities: list[str] = field(default_factory=list)


@dataclass
class RelationshipGraph:
    entities: dict[str, EntityRelationship]
    devices: dict[str, DeviceRelationship]
    integrations: dict[str, IntegrationRelationship]


def build_relationship_graph(model: HADocsModel) -> RelationshipGraph:
    entity_relations: dict[str, EntityRelationship] = {}
    device_relations: dict[str, DeviceRelationship] = {}
    integration_relations: dict[str, IntegrationRelationship] = {}

    for device in model.devices.values():
        integrations = sorted({entity.platform for entity in device.entities})
        important = sorted(entity.entity_id for entity in device.entities if entity.importance == "important")
        diagnostic = sorted(entity.entity_id for entity in device.entities if entity.importance == "diagnostic")
        ignored = sorted(entity.entity_id for entity in device.entities if entity.is_ignored)
        problems = sorted(
            entity.entity_id
            for entity in device.entities
            if entity.state in ("unknown", "unavailable")
            and not entity.is_ignored
            and entity.importance != "diagnostic"
        )

        device_relations[device.device_id] = DeviceRelationship(
            device_id=device.device_id,
            name=device.name,
            area_id=device.area_id,
            classification=device.classification,
            integrations=integrations,
            important_entities=important,
            diagnostic_entities=diagnostic,
            ignored_entities=ignored,
            problem_entities=problems,
        )

    for entity in model.entities.values():
        device = model.devices.get(entity.device_id or "")
        entity_relations[entity.entity_id] = EntityRelationship(
            entity_id=entity.entity_id,
            name=entity.name,
            domain=entity.domain,
            state=entity.state,
            area_id=entity.area_id,
            device_id=entity.device_id,
            device_name=device.name if device else "",
            integration=entity.platform,
            importance=entity.importance,
            is_ignored=entity.is_ignored,
        )

    for integration in model.integrations.values():
        devices = sorted({device.name for device in integration.devices})
        important = sorted(entity.entity_id for entity in integration.entities if entity.importance == "important")
        diagnostic = sorted(entity.entity_id for entity in integration.entities if entity.importance == "diagnostic")
        ignored = sorted(entity.entity_id for entity in integration.entities if entity.is_ignored)
        problems = sorted(
            entity.entity_id
            for entity in integration.entities
            if entity.state in ("unknown", "unavailable")
            and not entity.is_ignored
            and entity.importance != "diagnostic"
        )

        integration_relations[integration.platform] = IntegrationRelationship(
            platform=integration.platform,
            devices=devices,
            important_entities=important,
            diagnostic_entities=diagnostic,
            ignored_entities=ignored,
            problem_entities=problems,
        )

    return RelationshipGraph(
        entities=entity_relations,
        devices=device_relations,
        integrations=integration_relations,
    )


def top_problem_devices(graph: RelationshipGraph, limit: int = 20) -> list[DeviceRelationship]:
    devices = sorted(
        graph.devices.values(),
        key=lambda device: len(device.problem_entities),
        reverse=True,
    )
    return [device for device in devices if device.problem_entities][:limit]


def top_problem_integrations(graph: RelationshipGraph, limit: int = 20) -> list[IntegrationRelationship]:
    integrations = sorted(
        graph.integrations.values(),
        key=lambda integration: len(integration.problem_entities),
        reverse=True,
    )
    return [integration for integration in integrations if integration.problem_entities][:limit]
