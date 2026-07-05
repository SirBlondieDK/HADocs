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


@dataclass
class CollapsedIncident:
    incident_id: str
    title: str
    category: str
    severity: str
    root_cause: str
    affected_entities: list[str] = field(default_factory=list)
    affected_devices: list[str] = field(default_factory=list)
    affected_integrations: list[str] = field(default_factory=list)
    child_incidents: list[Incident] = field(default_factory=list)
    recommendation: str = ""
    estimated_score_gain: int = 0
    estimated_repair_minutes: int = 0

    @property
    def child_count(self) -> int:
        return len(self.child_incidents)

    @property
    def total_affected_entities(self) -> int:
        return len(set(self.affected_entities))

    @property
    def total_affected_devices(self) -> int:
        return len(set(self.affected_devices))


def _severity_from_count(count: int) -> str:
    if count >= 30:
        return "critical"
    if count >= 10:
        return "warning"
    if count >= 1:
        return "maintenance"
    return "info"


def _score_gain_from_count(count: int) -> int:
    if count >= 100:
        return 10
    if count >= 50:
        return 8
    if count >= 30:
        return 6
    if count >= 15:
        return 4
    if count >= 5:
        return 2
    if count >= 1:
        return 1
    return 0


def _repair_minutes(category: str, count: int) -> int:
    if category == "mobile_app_device":
        return 2
    if category == "mobile_app_group":
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


def _severity_rank(severity: str) -> int:
    return {
        "critical": 0,
        "warning": 1,
        "maintenance": 2,
        "info": 3,
    }.get(severity, 9)


def relevant_problem_entities(model: HADocsModel):
    return [
        entity for entity in model.entities.values()
        if entity.state in ("unknown", "unavailable")
        and not entity.is_ignored
        and entity.importance != "diagnostic"
    ]


def build_incidents(model: HADocsModel, graph: RelationshipGraph) -> list[Incident]:
    incidents: list[Incident] = []

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

        title = f"{device.name.strip()} has {count} relevant unavailable/unknown entities"
        if category == "mobile_app_device":
            title = f"Mobile App device appears offline: {device.name.strip()}"

        incidents.append(
            Incident(
                incident_id=f"device:{device_id}",
                title=title,
                category=category,
                severity=_severity_from_count(count),
                root_cause=device.name.strip(),
                affected_entities=sorted(e.entity_id for e in entities),
                affected_devices=[device.name.strip()],
                affected_integrations=sorted({e.platform for e in entities}),
                recommendation=_recommendation_for_device(device.name.strip(), category, count),
                estimated_score_gain=_score_gain_from_count(count),
                estimated_repair_minutes=_repair_minutes(category, count),
            )
        )

    problems_by_integration = defaultdict(list)
    for entity in relevant_problem_entities(model):
        problems_by_integration[entity.platform].append(entity)

    for platform, entities in problems_by_integration.items():
        count = len(entities)
        if count < 5:
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
                    model.devices[e.device_id].name.strip()
                    for e in entities
                    if e.device_id in model.devices
                }),
                affected_integrations=[platform],
                recommendation=_recommendation_for_integration(platform, count),
                estimated_score_gain=_score_gain_from_count(count),
                estimated_repair_minutes=_repair_minutes("integration", count),
            )
        )

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
                affected_devices=sorted(device.name.strip() for device in missing_area),
                recommendation="Assign physical devices to areas in Home Assistant.",
                estimated_score_gain=min(3, max(1, count // 15)),
                estimated_repair_minutes=_repair_minutes("missing_area", count),
            )
        )

    return sorted(
        incidents,
        key=lambda incident: (
            _severity_rank(incident.severity),
            -len(incident.affected_entities),
            -incident.estimated_score_gain,
        ),
    )


def collapse_incidents(incidents: list[Incident]) -> list[CollapsedIncident]:
    """Collapse child device incidents into parent integration incidents.

    This makes the report useful for real users: one Mobile App problem with
    three offline devices should appear as one top-level root cause, not four
    unrelated incidents.
    """
    integration_incidents = {
        incident.affected_integrations[0]: incident
        for incident in incidents
        if incident.category == "integration" and incident.affected_integrations
    }

    consumed_child_ids: set[str] = set()
    collapsed: list[CollapsedIncident] = []

    for platform, integration_incident in integration_incidents.items():
        child_candidates = [
            incident for incident in incidents
            if incident.incident_id != integration_incident.incident_id
            and platform in incident.affected_integrations
            and incident.category in {"physical_device", "mobile_app_device"}
        ]

        if not child_candidates:
            continue

        child_entity_count = sum(len(child.affected_entities) for child in child_candidates)
        parent_count = len(integration_incident.affected_entities)

        # Collapse if the children explain a meaningful part of the integration.
        # For mobile_app we always collapse, because device-level offline phones
        # are usually the actionable root cause.
        should_collapse = platform == "mobile_app" or child_entity_count >= parent_count * 0.45

        if not should_collapse:
            continue

        for child in child_candidates:
            consumed_child_ids.add(child.incident_id)

        affected_entities = sorted(set(integration_incident.affected_entities))
        affected_devices = sorted(set(integration_incident.affected_devices))
        severity = integration_incident.severity

        category = "mobile_app_group" if platform == "mobile_app" else "integration_group"
        title = integration_incident.title
        root_cause = integration_incident.root_cause
        repair_time = min(
            integration_incident.estimated_repair_minutes,
            max([child.estimated_repair_minutes for child in child_candidates] or [integration_incident.estimated_repair_minutes]),
        )

        if platform == "mobile_app":
            title = f"Mobile App: {len(child_candidates)} devices appear offline"
            root_cause = "Mobile App devices"
            repair_time = 2

        collapsed.append(
            CollapsedIncident(
                incident_id=f"collapsed:{platform}",
                title=title,
                category=category,
                severity=severity,
                root_cause=root_cause,
                affected_entities=affected_entities,
                affected_devices=affected_devices,
                affected_integrations=[platform],
                child_incidents=sorted(child_candidates, key=lambda item: len(item.affected_entities), reverse=True),
                recommendation=_recommendation_for_collapsed(platform, child_candidates, integration_incident),
                estimated_score_gain=min(integration_incident.estimated_score_gain, max([c.estimated_score_gain for c in child_candidates] or [1])),
                estimated_repair_minutes=repair_time,
            )
        )

    collapsed_parent_ids = {
        item.incident_id.replace("collapsed:", "integration:")
        for item in collapsed
    }

    for incident in incidents:
        if incident.incident_id in consumed_child_ids:
            continue
        if incident.incident_id in collapsed_parent_ids:
            continue

        collapsed.append(
            CollapsedIncident(
                incident_id=incident.incident_id,
                title=incident.title,
                category=incident.category,
                severity=incident.severity,
                root_cause=incident.root_cause,
                affected_entities=incident.affected_entities,
                affected_devices=incident.affected_devices,
                affected_integrations=incident.affected_integrations,
                child_incidents=[],
                recommendation=incident.recommendation,
                estimated_score_gain=incident.estimated_score_gain,
                estimated_repair_minutes=incident.estimated_repair_minutes,
            )
        )

    return sorted(
        collapsed,
        key=lambda incident: (
            _severity_rank(incident.severity),
            -len(incident.affected_entities),
            -incident.estimated_score_gain,
        ),
    )


def visible_incidents(collapsed_incidents: list[CollapsedIncident], limit: int = 12) -> list[CollapsedIncident]:
    critical_and_warning = [
        incident for incident in collapsed_incidents
        if incident.severity in {"critical", "warning"}
    ]
    maintenance = [
        incident for incident in collapsed_incidents
        if incident.severity == "maintenance"
    ]

    result = critical_and_warning[:limit]
    if len(result) < limit:
        result.extend(maintenance[: limit - len(result)])

    return result


def hidden_incident_count(collapsed_incidents: list[CollapsedIncident], limit: int = 12) -> int:
    return max(0, len(collapsed_incidents) - len(visible_incidents(collapsed_incidents, limit)))


def _recommendation_for_collapsed(platform: str, children: list[Incident], parent: Incident) -> str:
    if platform == "mobile_app":
        devices = ", ".join(child.root_cause for child in children[:5])
        return (
            f"Open the Home Assistant Companion App on the affected devices ({devices}), "
            "verify they can reach Home Assistant, then refresh or restart the app."
        )
    return parent.recommendation


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
    if platform == "hassio":
        return "Check the affected Home Assistant add-ons and supervisor entities."
    return f"Check the '{platform}' integration and its affected devices."
