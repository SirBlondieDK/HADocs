from dataclasses import dataclass, field
from collections import defaultdict

from src.hadocs.core.models import HADocsModel
from src.hadocs.core.relationships import RelationshipGraph


@dataclass
class Incident:
    incident_id: str
    title: str
    category: str
    severity: str
    root_cause: str
    affected_entities: list[str] = field(default_factory=list)
    affected_devices: list[str] = field(default_factory=list)
    affected_integrations: list[str] = field(default_factory=list)
    recommendation: str = ""
    estimated_score_gain: int = 0
    estimated_repair_minutes: int = 0


def _severity_from_count(count: int) -> str:
    if count >= 30:
        return "critical"
    if count >= 10:
        return "warning"
    if count >= 1:
        return "maintenance"
    return "info"


def _score_gain_from_count(count: int) -> int:
    if count >= 50:
        return 10
    if count >= 30:
        return 8
    if count >= 15:
        return 5
    if count >= 5:
        return 3
    if count >= 1:
        return 1
    return 0


def _repair_minutes(category: str, count: int) -> int:
    if category == "mobile_app_device":
        return 2
    if category == "integration":
        return 10
    if category == "physical_device":
        return 5
    if category == "missing_area":
        return max(1, min(10, count // 2))
    if category == "duplicates":
        return max(1, min(8, count))
    return 3


def relevant_problem_entities(model: HADocsModel):
    return [
        entity for entity in model.entities.values()
        if entity.state in ("unknown", "unavailable")
        and not entity.is_ignored
        and entity.importance != "diagnostic"
    ]


def build_incidents(model: HADocsModel, graph: RelationshipGraph) -> list[Incident]:
    incidents: list[Incident] = []

    # Device-level root causes.
    problems_by_device = defaultdict(list)
    for entity in relevant_problem_entities(model):
        key = entity.device_id or "_no_device"
        problems_by_device[key].append(entity)

    for device_id, entities in problems_by_device.items():
        if device_id == "_no_device":
            continue

        device = model.devices.get(device_id)
        if not device:
            continue

        count = len(entities)
        if count == 0:
            continue

        category = "mobile_app_device" if any(e.platform == "mobile_app" for e in entities) else "physical_device"

        title = f"{device.name} has {count} relevant unavailable/unknown entities"
        if category == "mobile_app_device":
            title = f"Mobile App device appears offline: {device.name}"

        incidents.append(
            Incident(
                incident_id=f"device:{device_id}",
                title=title,
                category=category,
                severity=_severity_from_count(count),
                root_cause=device.name,
                affected_entities=sorted(e.entity_id for e in entities),
                affected_devices=[device.name],
                affected_integrations=sorted({e.platform for e in entities}),
                recommendation=_recommendation_for_device(device.name, category, count),
                estimated_score_gain=_score_gain_from_count(count),
                estimated_repair_minutes=_repair_minutes(category, count),
            )
        )

    # Integration-level root causes.
    problems_by_integration = defaultdict(list)
    for entity in relevant_problem_entities(model):
        problems_by_integration[entity.platform].append(entity)

    for platform, entities in problems_by_integration.items():
        count = len(entities)
        if count < 5:
            continue

        # Avoid duplicating integrations where one device explains almost everything.
        largest_device_count = 0
        by_device = defaultdict(int)
        for entity in entities:
            by_device[entity.device_id or "_no_device"] += 1
        if by_device:
            largest_device_count = max(by_device.values())

        if largest_device_count >= count * 0.8:
            continue

        incidents.append(
            Incident(
                incident_id=f"integration:{platform}",
                title=f"Integration issue: {platform}",
                category="integration",
                severity=_severity_from_count(count),
                root_cause=platform,
                affected_entities=sorted(e.entity_id for e in entities),
                affected_devices=sorted({
                    model.devices[e.device_id].name
                    for e in entities
                    if e.device_id in model.devices
                }),
                affected_integrations=[platform],
                recommendation=_recommendation_for_integration(platform, count),
                estimated_score_gain=_score_gain_from_count(count),
                estimated_repair_minutes=_repair_minutes("integration", count),
            )
        )

    # Missing area incident.
    missing_area = [
        device for device in model.devices.values()
        if device.is_physical and (not device.area_id or device.area_id == "_uden_område")
    ]
    if missing_area:
        count = len(missing_area)
        incidents.append(
            Incident(
                incident_id="maintenance:missing_area",
                title=f"{count} physical devices are missing an area",
                category="missing_area",
                severity="maintenance",
                root_cause="Area assignment",
                affected_devices=sorted(device.name for device in missing_area),
                recommendation="Assign physical devices to areas in Home Assistant.",
                estimated_score_gain=min(4, max(1, count // 12)),
                estimated_repair_minutes=_repair_minutes("missing_area", count),
            )
        )

    return sorted(
        incidents,
        key=lambda incident: (
            {"critical": 0, "warning": 1, "maintenance": 2, "info": 3}.get(incident.severity, 9),
            -len(incident.affected_entities),
            -incident.estimated_score_gain,
        ),
    )


def _recommendation_for_device(name: str, category: str, count: int) -> str:
    if category == "mobile_app_device":
        return (
            f"Open the Home Assistant Companion App on '{name}', make sure it can reach Home Assistant, "
            "and refresh/restart the app if needed."
        )

    return (
        f"Check whether '{name}' is powered on, connected, and still available in its integration. "
        "If it is intentionally removed, clean it up in Home Assistant."
    )


def _recommendation_for_integration(platform: str, count: int) -> str:
    if platform in {"mqtt", "zigbee2mqtt"}:
        return "Check MQTT broker, Zigbee2MQTT bridge, and whether affected devices are online."
    if platform == "frigate":
        return "Check Frigate container status, camera streams, and detector health."
    if platform == "wled":
        return "Check whether the WLED controller is powered and reachable on the network."
    if platform == "mobile_app":
        return "Open the affected Companion Apps and verify they can reach Home Assistant."
    return f"Check the '{platform}' integration and its affected devices."
