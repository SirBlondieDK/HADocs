from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from src.hadocs.core.device_reachability import (
    ReachabilityResult,
    ReachabilityStatus,
    determine_device_reachability,
)
from src.hadocs.core.models import (
    DeviceModel,
    EntityModel,
    InstallationModel,
)
from src.hadocs.core.state_interpreter import (
    StateInterpretation,
    StateMeaning,
    interpret_entity_state,
)


@dataclass(frozen=True, slots=True)
class EntityEvidence:
    entity: EntityModel
    interpretation: StateInterpretation


@dataclass(frozen=True, slots=True)
class DeviceEvidence:
    device: DeviceModel
    reachability: ReachabilityResult
    faults: tuple[EntityEvidence, ...] = ()
    transients: tuple[EntityEvidence, ...] = ()
    expected: tuple[EntityEvidence, ...] = ()


@dataclass(slots=True)
class IncidentV2:
    incident_id: str
    title: str
    category: str
    severity: str
    root_cause: str
    confidence: int
    affected_entities: list[str] = field(default_factory=list)
    affected_devices: list[str] = field(default_factory=list)
    affected_integrations: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""


def collect_device_evidence(
    device: DeviceModel,
) -> DeviceEvidence:
    """Collect interpreted state and reachability evidence for one device."""

    faults: list[EntityEvidence] = []
    transients: list[EntityEvidence] = []
    expected: list[EntityEvidence] = []

    for entity in device.entities:
        interpretation = interpret_entity_state(entity)
        item = EntityEvidence(
            entity=entity,
            interpretation=interpretation,
        )

        if interpretation.meaning is StateMeaning.FAULT:
            faults.append(item)
        elif interpretation.meaning is StateMeaning.TRANSIENT:
            transients.append(item)
        elif interpretation.meaning in {
            StateMeaning.EXPECTED_UNKNOWN,
            StateMeaning.EXPECTED_UNAVAILABLE,
            StateMeaning.IGNORED,
        }:
            expected.append(item)

    return DeviceEvidence(
        device=device,
        reachability=determine_device_reachability(device),
        faults=tuple(faults),
        transients=tuple(transients),
        expected=tuple(expected),
    )


def _severity_for_device(
    evidence: DeviceEvidence,
) -> str | None:
    """Determine severity from positive fault evidence, not raw counts."""

    reachability = evidence.reachability

    if (
        reachability.status is ReachabilityStatus.OFFLINE
        and reachability.confidence >= 90
    ):
        return "critical"

    if reachability.status is ReachabilityStatus.OFFLINE:
        return "warning"

    important_faults = [
        item
        for item in evidence.faults
        if item.entity.importance == "important"
    ]

    if important_faults:
        return "warning"

    if evidence.faults:
        return "maintenance"

    return None


def _device_recommendation(
    evidence: DeviceEvidence,
) -> str:
    if evidence.reachability.status is ReachabilityStatus.OFFLINE:
        return (
            "Check device power, network or radio connectivity, "
            "and the parent integration."
        )

    return (
        "Check the unavailable primary entities and verify that "
        "the device still reports through Home Assistant."
    )


def build_device_incidents_v2(
    model: InstallationModel,
) -> list[IncidentV2]:
    """Build evidence-based device incidents."""

    incidents: list[IncidentV2] = []

    for device in model.devices.values():
        if not device.is_physical:
            continue

        evidence = collect_device_evidence(device)
        severity = _severity_for_device(evidence)

        if severity is None:
            continue

        fault_entities = [
            item.entity.entity_id
            for item in evidence.faults
        ]

        platforms = sorted({
            item.entity.platform
            for item in evidence.faults
        })

        if not platforms:
            platforms = sorted({
                entity.platform
                for entity in device.entities
                if entity.platform
            })

        evidence_lines = [
            evidence.reachability.reason,
            *evidence.reachability.evidence,
        ]

        if evidence.faults:
            evidence_lines.append(
                f"{len(evidence.faults)} confirmed entity fault(s)."
            )

        incidents.append(
            IncidentV2(
                incident_id=f"device-v2:{device.device_id}",
                title=f"Device issue: {device.name}",
                category="physical_device",
                severity=severity,
                root_cause=device.name,
                confidence=evidence.reachability.confidence,
                affected_entities=sorted(fault_entities),
                affected_devices=[device.name],
                affected_integrations=platforms,
                evidence=evidence_lines,
                recommendation=_device_recommendation(evidence),
            )
        )

    return incidents


def build_integration_incidents_v2(
    model: InstallationModel,
    device_incidents: list[IncidentV2],
) -> list[IncidentV2]:
    """Create integration incidents from actual affected devices."""

    incidents_by_platform: dict[str, list[IncidentV2]] = defaultdict(list)

    for incident in device_incidents:
        for platform in incident.affected_integrations:
            incidents_by_platform[platform].append(incident)

    integration_incidents: list[IncidentV2] = []

    for platform, children in incidents_by_platform.items():
        integration = model.integrations.get(platform)
        if integration is None:
            continue

        affected_devices = sorted({
            device_name
            for child in children
            for device_name in child.affected_devices
        })

        affected_entities = sorted({
            entity_id
            for child in children
            for entity_id in child.affected_entities
        })

        explicit_critical = [
            child
            for child in children
            if (
                child.severity == "critical"
                and child.confidence >= 90
            )
        ]

        if explicit_critical and len(affected_devices) >= 2:
            severity = "critical"
        elif any(
            child.severity in {"critical", "warning"}
            for child in children
        ):
            severity = "warning"
        else:
            severity = "maintenance"

        confidence = max(
            (child.confidence for child in children),
            default=0,
        )

        integration_incidents.append(
            IncidentV2(
                incident_id=f"integration-v2:{platform}",
                title=f"Integration issue: {platform}",
                category="integration",
                severity=severity,
                root_cause=platform,
                confidence=confidence,
                affected_entities=affected_entities,
                affected_devices=affected_devices,
                affected_integrations=[platform],
                evidence=[
                    (
                        f"{len(affected_devices)} device(s) have "
                        "evidence-based incidents."
                    ),
                    (
                        f"{len(integration.entities)} total entities "
                        "were not used as a severity multiplier."
                    ),
                ],
                recommendation=(
                    f"Check the {platform} integration and the affected "
                    "devices. Diagnose the parent integration only when "
                    "multiple devices share the same failure."
                ),
            )
        )

    return integration_incidents


def build_incidents_v2(
    model: InstallationModel,
) -> list[IncidentV2]:
    """Build evidence-based device and integration incidents."""

    device_incidents = build_device_incidents_v2(model)
    integration_incidents = build_integration_incidents_v2(
        model,
        device_incidents,
    )

    severity_rank = {
        "critical": 0,
        "warning": 1,
        "maintenance": 2,
        "info": 3,
    }

    return sorted(
        [*device_incidents, *integration_incidents],
        key=lambda incident: (
            severity_rank.get(incident.severity, 9),
            -incident.confidence,
            incident.root_cause.lower(),
        ),
    )
