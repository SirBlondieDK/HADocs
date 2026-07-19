from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from src.hadocs.core.device_overrides import DeviceOverride, get_device_policy
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
from src.hadocs.intelligence.engine import profile_entity
from src.hadocs.intelligence.freshness import (
    FreshnessResult,
    FreshnessStatus,
    determine_entity_freshness,
)
from src.hadocs.intelligence.profiles import ProfileKind


@dataclass(frozen=True, slots=True)
class EntityEvidence:
    entity: EntityModel
    interpretation: StateInterpretation
    freshness: FreshnessResult


@dataclass(frozen=True, slots=True)
class DeviceEvidence:
    device: DeviceModel
    reachability: ReachabilityResult
    expected_offline: bool = False
    external: bool = False
    override_reason: str = ""
    faults: tuple[EntityEvidence, ...] = ()
    transients: tuple[EntityEvidence, ...] = ()
    expected: tuple[EntityEvidence, ...] = ()
    stale: tuple[EntityEvidence, ...] = ()
    very_stale: tuple[EntityEvidence, ...] = ()


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

    # Compatibility fields used by the existing advisor and report pipeline.
    estimated_score_gain: int = 0
    estimated_repair_minutes: int = 15
    child_incidents: list["IncidentV2"] = field(default_factory=list)

    @property
    def child_count(self) -> int:
        return len(self.child_incidents)


def _estimated_score_gain(severity: str, *, integration: bool = False) -> int:
    if integration:
        return {
            "critical": 10,
            "warning": 6,
            "maintenance": 3,
        }.get(severity, 1)

    return {
        "critical": 8,
        "warning": 5,
        "maintenance": 2,
    }.get(severity, 1)


def _estimated_repair_minutes(
    severity: str,
    *,
    integration: bool = False,
) -> int:
    if integration:
        return {
            "critical": 45,
            "warning": 30,
            "maintenance": 15,
        }.get(severity, 10)

    return {
        "critical": 30,
        "warning": 20,
        "maintenance": 10,
    }.get(severity, 10)


def collect_device_evidence(
    device: DeviceModel,
    overrides: tuple[DeviceOverride, ...] = (),
) -> DeviceEvidence:
    """Collect interpreted state, freshness and reachability evidence."""
    policy = get_device_policy(device, overrides)

    faults: list[EntityEvidence] = []
    transients: list[EntityEvidence] = []
    expected: list[EntityEvidence] = []
    stale: list[EntityEvidence] = []
    very_stale: list[EntityEvidence] = []

    for entity in device.entities:
        profile = profile_entity(entity)
        interpretation = interpret_entity_state(entity)
        freshness = determine_entity_freshness(entity)

        item = EntityEvidence(
            entity=entity,
            interpretation=interpretation,
            freshness=freshness,
        )

        if (
            profile.affects_health
            and profile.kind is not ProfileKind.DIAGNOSTIC
            and not policy.ignore_stale
            and not policy.expected_offline
            and policy.ownership != "external"
        ):
            if freshness.status is FreshnessStatus.VERY_STALE:
                very_stale.append(item)
            elif freshness.status is FreshnessStatus.STALE:
                stale.append(item)

        if (
            interpretation.meaning is StateMeaning.FAULT
            and not policy.expected_offline
            and policy.ownership != "external"
        ):
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
        reachability=determine_device_reachability(device, overrides),
        expected_offline=policy.expected_offline,
        external=policy.ownership == "external",
        override_reason=policy.reason,
        faults=tuple(faults),
        transients=tuple(transients),
        expected=tuple(expected),
        stale=tuple(stale),
        very_stale=tuple(very_stale),
    )


def _severity_for_device(
    evidence: DeviceEvidence,
) -> str | None:
    """Determine severity from positive fault and freshness evidence."""
    if evidence.external:
        return None

    if evidence.expected_offline:
        return "maintenance"

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

    if evidence.expected_offline:
        return (
            "Device is intentionally offline by user override. "
            "Disable the override when it should be active again."
        )

    if evidence.very_stale:
        return "maintenance"

    return None


def _device_recommendation(
    evidence: DeviceEvidence,
) -> str:
    if evidence.very_stale:
        return (
            "Verify whether this device is still in use. If it has been "
            "retired, remove or disable its stale Home Assistant entities. "
            "Otherwise restore connectivity and run HADocs again."
        )

    if evidence.reachability.status is ReachabilityStatus.OFFLINE:
        return (
            "Check device power, network or radio connectivity, and the "
            "parent integration."
        )

    return (
        "Check the unavailable primary entities and verify that the device "
        "still reports through Home Assistant."
    )


def _freshness_evidence_lines(
    evidence: DeviceEvidence,
) -> list[str]:
    lines: list[str] = []

    if evidence.very_stale:
        lines.append(
            f"{len(evidence.very_stale)} primary entity report(s) are "
            "very stale."
        )

    if evidence.stale:
        lines.append(
            f"{len(evidence.stale)} primary entity report(s) are stale."
        )

    examples = [
        *evidence.very_stale,
        *evidence.stale,
    ][:5]

    for item in examples:
        age = item.freshness.age_seconds
        if age is None:
            continue

        days = age // 86400
        lines.append(
            f"{item.entity.entity_id}: "
            f"{item.freshness.status.value}, about {days} day(s) old."
        )

    return lines


def build_device_incidents_v2(
    model: InstallationModel,
    overrides: tuple[DeviceOverride, ...] = (),
) -> list[IncidentV2]:
    """Build evidence-based device incidents."""

    incidents: list[IncidentV2] = []

    for device in model.devices.values():
        if not device.is_physical:
            continue

        evidence = collect_device_evidence(device, overrides)
        severity = _severity_for_device(evidence)

        if severity is None:
            continue

        fault_entities = {
            item.entity.entity_id
            for item in evidence.faults
        }
        stale_entities = {
            item.entity.entity_id
            for item in [
                *evidence.very_stale,
                *evidence.stale,
            ]
        }
        affected_entity_ids = sorted(
            fault_entities | stale_entities
        )

        platforms = sorted({
            item.entity.platform
            for item in [
                *evidence.faults,
                *evidence.very_stale,
                *evidence.stale,
            ]
            if item.entity.platform
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
            *_freshness_evidence_lines(evidence),
        ]

        if evidence.expected_offline:
            evidence_lines.append("User override marks this device as intentionally offline.")
            if evidence.override_reason:
                evidence_lines.append(f"Override reason: {evidence.override_reason}")

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
                confidence=max(
                    evidence.reachability.confidence,
                    95 if evidence.very_stale else 0,
                ),
                affected_entities=affected_entity_ids,
                affected_devices=[device.name],
                affected_integrations=platforms,
                evidence=evidence_lines,
                recommendation=_device_recommendation(evidence),
                estimated_score_gain=_estimated_score_gain(severity),
                estimated_repair_minutes=_estimated_repair_minutes(severity),
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
                        f"{len(integration.entities)} total entities were "
                        "not used as a severity multiplier."
                    ),
                ],
                recommendation=(
                    f"Check the {platform} integration and the affected "
                    "devices. Diagnose the parent integration only when "
                    "multiple devices share the same failure."
                ),
                estimated_score_gain=_estimated_score_gain(
                    severity,
                    integration=True,
                ),
                estimated_repair_minutes=_estimated_repair_minutes(
                    severity,
                    integration=True,
                ),
                child_incidents=list(children),
            )
        )

    return integration_incidents


def build_incidents_v2(
    model: InstallationModel,
    overrides: tuple[DeviceOverride, ...] = (),
) -> list[IncidentV2]:
    """Build evidence-based device and integration incidents."""

    device_incidents = build_device_incidents_v2(model, overrides)
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
