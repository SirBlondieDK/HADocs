from src.hadocs.core.models import DeviceHealth, HADocsModel


CRITICAL_PATTERNS = [
    "homeassistant_status", "hp_mini_status", "adguard_status",
    "zigbee2mqtt_status", "zigbee2mqtt_bridge_connection_state",
    "frigate_status", "remote_ui", "internet_online", "deco_online",
]


def calculate_device_health(model: HADocsModel) -> list[DeviceHealth]:
    results: list[DeviceHealth] = []

    for device in model.devices.values():
        if not device.is_physical:
            continue

        relevant_entities = [
            entity for entity in device.entities
            if not entity.is_ignored and entity.is_physical and entity.importance != "diagnostic"
        ]

        if not relevant_entities:
            continue

        unavailable = [e for e in relevant_entities if e.state == "unavailable"]
        unknown = [e for e in relevant_entities if e.state == "unknown"]

        score = 100
        reasons = []

        if unavailable:
            important_count = sum(1 for e in unavailable if e.importance == "important")
            normal_count = len(unavailable) - important_count
            penalty = min(55, important_count * 10 + normal_count * 3)
            score -= penalty
            reasons.append(f"{len(unavailable)} relevant entities unavailable")

        if unknown:
            important_count = sum(1 for e in unknown if e.importance == "important")
            normal_count = len(unknown) - important_count
            penalty = min(25, important_count * 5 + normal_count)
            score -= penalty
            reasons.append(f"{len(unknown)} relevant entities unknown")

        battery_entities = [e for e in relevant_entities if "battery" in e.entity_id.lower()]
        for entity in battery_entities:
            try:
                value = float(entity.state)
                if value <= 10:
                    score -= 12
                    reasons.append(f"{entity.entity_id} battery critical ({value}%)")
                elif value <= 25:
                    score -= 4
                    reasons.append(f"{entity.entity_id} battery low ({value}%)")
            except Exception:
                pass

        score = max(0, min(100, score))

        if score >= 85:
            status = "healthy"
        elif score >= 55:
            status = "warning"
        else:
            status = "problem"

        results.append(DeviceHealth(device=device, status=status, score=score, reasons=reasons))

    return results


def calculate_health_score(model: HADocsModel, device_health: list[DeviceHealth]) -> tuple[int, list[str]]:
    score = 100
    notes = []

    problem_devices = [d for d in device_health if d.status == "problem"]
    warning_devices = [d for d in device_health if d.status == "warning"]

    if problem_devices:
        penalty = min(30, len(problem_devices) * 5)
        score -= penalty
        notes.append(f"{len(problem_devices)} physical devices have serious problems (-{penalty})")

    if warning_devices:
        penalty = min(15, len(warning_devices) * 2)
        score -= penalty
        notes.append(f"{len(warning_devices)} physical devices have warnings (-{penalty})")

    physical_without_area = [
        d for d in model.devices.values()
        if d.is_physical and (not d.area_id or d.area_id == "_uden_område")
    ]
    if physical_without_area:
        penalty = min(6, max(1, len(physical_without_area) // 10))
        score -= penalty
        notes.append(f"{len(physical_without_area)} physical devices have no area (-{penalty})")

    duplicate_domain_names = find_duplicate_names_by_domain(model)
    if duplicate_domain_names:
        penalty = min(2, max(1, len(duplicate_domain_names) // 15))
        score -= penalty
        notes.append(f"{len(duplicate_domain_names)} duplicate names within same domain (-{penalty})")

    ignored_bad = [
        e for e in model.entities.values()
        if e.is_ignored and e.state in ("unknown", "unavailable")
    ]
    if ignored_bad:
        notes.append(f"{len(ignored_bad)} ignored diagnostic/system entities are unknown/unavailable")

    return max(0, min(100, score)), notes


def find_duplicate_names_by_domain(model: HADocsModel) -> dict[tuple[str, str], list[str]]:
    grouped: dict[tuple[str, str], list[str]] = {}

    for entity in model.entities.values():
        if entity.is_ignored or entity.importance == "diagnostic":
            continue
        if entity.domain in {"device_tracker", "sensor"}:
            continue
        key = (entity.domain, entity.name)
        grouped.setdefault(key, []).append(entity.entity_id)

    return {key: value for key, value in grouped.items() if len(value) > 1}


def get_critical_entities(model: HADocsModel):
    critical = []
    for entity in model.entities.values():
        if entity.state not in ("unknown", "unavailable"):
            continue
        if entity.is_ignored or entity.importance == "diagnostic":
            continue
        eid = entity.entity_id.lower()
        if any(pattern in eid for pattern in CRITICAL_PATTERNS):
            critical.append(entity)
    return critical

# ---------------------------------------------------------------------------
# Health Engine v2
# ---------------------------------------------------------------------------

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthScoreBreakdown:
    score: int
    potential_score: int
    grade: str
    status: str
    enabled_entities: int
    disabled_entities_ignored: int
    affected_active_entities: int
    normalized_penalty: int
    severity_penalty: int
    root_cause_penalty: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "score": self.score,
            "potential_score": self.potential_score,
            "grade": self.grade,
            "status": self.status,
            "enabled_entities": self.enabled_entities,
            "disabled_entities_ignored": self.disabled_entities_ignored,
            "affected_active_entities": self.affected_active_entities,
            "normalized_penalty": self.normalized_penalty,
            "severity_penalty": self.severity_penalty,
            "root_cause_penalty": self.root_cause_penalty,
        }


def _hs_get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _hs_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    return []


def is_disabled_entity(entity: Any) -> bool:
    disabled_by = _hs_get(entity, "disabled_by")
    if disabled_by:
        return True

    registry = _hs_get(entity, "entity_registry", {})
    if isinstance(registry, dict) and registry.get("disabled_by"):
        return True

    if bool(_hs_get(entity, "disabled", False)):
        return True

    state = str(_hs_get(entity, "state", "")).lower()
    return state in {"disabled", "unavailable_disabled"}


def _hs_severity(incident: Any) -> str:
    severity = str(_hs_get(incident, "severity", "")).lower()
    if severity in {"critical", "error"}:
        return "critical"
    if severity in {"warning", "warn"}:
        return "warning"
    return "maintenance"


def _hs_entity_key(entity: Any) -> str:
    return str(
        _hs_get(entity, "entity_id", None)
        or _hs_get(entity, "id", None)
        or _hs_get(entity, "unique_id", None)
        or entity
    )


def calculate_health_score_v2(model: Any, incidents: list[Any]) -> HealthScoreBreakdown:
    """Calculate a size-normalized health score.

    v2.1 calibration notes:
    - Large Home Assistant installations should not be pushed toward 25/100
      just because one integration/root cause touches many entities.
    - Affected entities are still visible in the breakdown, but they are a
      smaller penalty than severity and root-cause count.
    - Disabled entities are ignored as problems.
    """

    entities = _hs_list(_hs_get(model, "entities", []))
    enabled_entities = [entity for entity in entities if not is_disabled_entity(entity)]
    disabled_entities = max(0, len(entities) - len(enabled_entities))
    enabled_count = max(1, len(enabled_entities))

    affected_active: set[str] = set()
    disabled_problem_entities = 0

    for incident in incidents or []:
        for entity in _hs_list(_hs_get(incident, "affected_entities", [])):
            if is_disabled_entity(entity):
                disabled_problem_entities += 1
                continue
            affected_active.add(_hs_entity_key(entity))

    affected_count = len(affected_active)

    # Large-installation calibration:
    # Use ratio against enabled entities, not sqrt(enabled_entities).
    # This prevents large installs with many related entities from being
    # scored as critical when only a small percentage is actually affected.
    affected_ratio = affected_count / max(1, enabled_count)
    normalized_penalty = min(10, round(affected_ratio * 22))

    critical = 0
    warning = 0
    maintenance = 0

    for incident in incidents or []:
        severity = _hs_severity(incident)
        if severity == "critical":
            critical += 1
        elif severity == "warning":
            warning += 1
        else:
            maintenance += 1

    # Severity still matters, but it should not dominate the whole score.
    severity_penalty = min(12, round(critical * 1.2 + warning * 0.8 + maintenance * 0.35))

    # Root causes indicate cleanup scope. Keep this capped so 15-20 root causes
    # is "needs attention", not automatically "critical".
    root_cause_penalty = min(6, round(len(incidents or []) * 0.25))

    total_penalty = min(45, normalized_penalty + severity_penalty + root_cause_penalty)
    score = max(45, 100 - total_penalty)

    # Potential score is the expected outcome after the top fixes, not a second
    # full recalculation. Keep it optimistic but bounded.
    potential_gain = min(18, 8 + critical + max(0, warning // 2))
    potential_score = min(100, score + potential_gain)

    if score >= 90:
        grade, status = "A", "Excellent"
    elif score >= 80:
        grade, status = "B", "Healthy"
    elif score >= 65:
        grade, status = "C", "Needs attention"
    elif score >= 50:
        grade, status = "D", "Degraded"
    else:
        grade, status = "E", "Critical"

    return HealthScoreBreakdown(
        score=int(score),
        potential_score=int(potential_score),
        grade=grade,
        status=status,
        enabled_entities=int(enabled_count),
        disabled_entities_ignored=int(disabled_problem_entities or disabled_entities),
        affected_active_entities=int(affected_count),
        normalized_penalty=int(normalized_penalty),
        severity_penalty=int(severity_penalty),
        root_cause_penalty=int(root_cause_penalty),
    )


def apply_health_score_v2(model: Any, executive: Any, incidents: list[Any]) -> Any:
    breakdown = calculate_health_score_v2(model, incidents)
    data = breakdown.as_dict()

    if isinstance(executive, dict):
        executive["score"] = breakdown.score
        executive["potential_score"] = breakdown.potential_score
        executive["health_score_v2"] = data
        executive["health_grade"] = breakdown.grade
        executive["health_status_v2"] = breakdown.status
        return executive

    values = {
        "score": breakdown.score,
        "potential_score": breakdown.potential_score,
        "health_score_v2": data,
        "health_grade": breakdown.grade,
        "health_status_v2": breakdown.status,
    }

    for key, value in values.items():
        try:
            setattr(executive, key, value)
        except Exception:
            pass

    return executive
