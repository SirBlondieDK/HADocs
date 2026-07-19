from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from src.hadocs.core.device_overrides import DeviceOverride, get_device_policy
from src.hadocs.core.health import is_disabled_entity
from src.hadocs.core.incidents import Incident
from src.hadocs.core.models import HADocsModel


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


_HASSIO_ROOTS = {"hassio", "supervisor", "home_assistant_supervisor"}
_HASSIO_CENTRAL_MARKERS = (
    "supervisor",
    "home_assistant_host",
    "home_assistant_core",
    "home_assistant_operating_system",
)
_HASSIO_HARD_FAILURE_MARKERS = (
    "supervisor",
    "home_assistant_host",
    "home_assistant_core",
)


def _normalised_root_cause(incident: Incident) -> str:
    return str(incident.root_cause or "").strip().lower().replace("-", "_")


def _hassio_severity(model: HADocsModel, entity_ids: list[str]) -> tuple[str, int]:
    """Calibrate Supervisor/Hassio severity from central runtime signals.

    Add-on helper sensors frequently become unknown during reloads, startup, or
    collector timing differences. Their quantity must not make the whole
    Supervisor integration critical. Critical is reserved for a confirmed
    unavailable Core, Supervisor, or Host signal.
    """
    central_unknown = 0
    central_unavailable = 0
    hard_failures = 0

    for entity_id in entity_ids:
        lowered = entity_id.lower()
        if not any(marker in lowered for marker in _HASSIO_CENTRAL_MARKERS):
            continue

        entity = model.entities.get(entity_id)
        state = str(getattr(entity, "state", "") or "").strip().lower()
        if state not in {"unknown", "unavailable"}:
            continue

        if state == "unknown":
            central_unknown += 1
        elif state == "unavailable":
            central_unavailable += 1
            if any(marker in lowered for marker in _HASSIO_HARD_FAILURE_MARKERS):
                hard_failures += 1

    if hard_failures:
        return "critical", min(4, max(1, hard_failures * 2))
    if central_unavailable:
        return "warning", min(2, max(1, central_unavailable))
    # Unknown is weak evidence. It can happen while the Supervisor reloads,
    # while helper sensors update, or when a status entity is optional. Do not
    # label a running Home Assistant installation as degraded from unknown alone.
    if central_unknown:
        return "maintenance", 1
    return "maintenance", 1


def _calibrated_incident_fields(
    model: HADocsModel, incident: Incident, entity_ids: list[str]
) -> tuple[str, int, str, str]:
    severity = _severity_from_count(len(entity_ids))
    score_gain = _score_gain_from_count(len(entity_ids))
    title = _updated_title(incident, len(entity_ids))
    recommendation = incident.recommendation

    if incident.category == "integration" and _normalised_root_cause(incident) in _HASSIO_ROOTS:
        severity, score_gain = _hassio_severity(model, entity_ids)
        if severity == "critical":
            title = "Home Assistant runtime outage detected"
            recommendation = (
                "A Core, Supervisor, or Host status signal is unavailable. "
                "Open Home Assistant System information and Supervisor logs, "
                "confirm the runtime component is online, then scan again."
            )
        elif severity == "warning":
            title = "Home Assistant runtime status needs review"
            recommendation = (
                "At least one central runtime status signal is unavailable, but no "
                "confirmed hard Core, Supervisor, or Host outage was found. Verify "
                "System information and Supervisor logs before taking action."
            )
        else:
            title = "Supervisor status sensors need review"
            recommendation = (
                "No confirmed Core, Supervisor, or Host outage was detected. "
                "The finding is based on unknown add-on or runtime helper sensors; "
                "treat it as maintenance and verify only the listed sensors."
            )

    return severity, score_gain, title, recommendation


def _entity_is_suppressed(model: HADocsModel, entity_id: str, overrides: tuple[DeviceOverride, ...]) -> bool:
    entity = model.entities.get(entity_id)
    if entity is None:
        return False
    if is_disabled_entity(entity):
        return True
    if not entity.device_id:
        return False
    device = model.devices.get(entity.device_id)
    if device is None:
        return False
    policy = get_device_policy(device, overrides)
    return policy.expected_offline or policy.ownership == "external"


def _remaining_device_names(model: HADocsModel, entity_ids: list[str]) -> list[str]:
    names: set[str] = set()
    for entity_id in entity_ids:
        entity = model.entities.get(entity_id)
        if entity is None or not entity.device_id:
            continue
        device = model.devices.get(entity.device_id)
        if device is not None and device.name:
            names.add(device.name.strip())
    return sorted(names)


def _updated_title(incident: Incident, count: int) -> str:
    if incident.category == "physical_device":
        return f"{incident.root_cause.strip() or 'Device'} has {count} relevant unavailable/unknown entities"
    return incident.title


def filter_effective_incidents(model: HADocsModel, incidents: Iterable[Incident], overrides: Iterable[DeviceOverride] = ()) -> list[Incident]:
    """Return only actionable incidents after disabled/override suppression.

    Apply this to raw incidents before collapse and executive-summary creation so
    every report, recommendation, score forecast and history snapshot uses the
    same effective incident set.
    """
    active_overrides = tuple(overrides)
    effective: list[Incident] = []

    for incident in incidents:
        entity_ids = list(dict.fromkeys(incident.affected_entities))
        if not entity_ids:
            effective.append(incident)
            continue

        remaining_entities = [
            entity_id for entity_id in entity_ids
            if not _entity_is_suppressed(model, entity_id, active_overrides)
        ]
        count = len(remaining_entities)
        if count == 0:
            continue
        if incident.category == "integration" and count < 5:
            continue

        affected_devices = _remaining_device_names(model, remaining_entities)
        if not affected_devices and incident.category not in {"physical_device", "mobile_app_device"}:
            affected_devices = list(incident.affected_devices)

        severity, score_gain, title, recommendation = _calibrated_incident_fields(
            model, incident, remaining_entities
        )

        effective.append(replace(
            incident,
            title=title,
            severity=severity,
            affected_entities=remaining_entities,
            affected_devices=affected_devices,
            recommendation=recommendation,
            estimated_score_gain=score_gain,
        ))

    return effective
