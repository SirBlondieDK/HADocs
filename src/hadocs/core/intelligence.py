from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ForecastStep:
    title: str
    root_cause: str
    score_gain: int
    repair_minutes: int
    health_after: int
    impact_score: int
    impact_label: str

    def as_dict(self) -> dict[str, int | str]:
        return self.__dict__.copy()


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    return []


def _num(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _severity(incident: Any) -> str:
    severity = str(_get(incident, "severity", "")).lower()
    if severity in {"critical", "error"}:
        return "critical"
    if severity in {"warning", "warn"}:
        return "warning"
    return "maintenance"


def _root(incident: Any) -> str:
    return str(_get(incident, "root_cause", _get(incident, "title", "Issue")))


def _title(incident: Any) -> str:
    return str(_get(incident, "title", _root(incident)))


def _affected_entities(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "affected_entities", []))


def _affected_devices(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "affected_devices", []))


def _children(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "children", [])) or _as_list(_get(incident, "child_incidents", []))


def calculate_impact_score(incident: Any) -> int:
    entities = len(_affected_entities(incident))
    devices = len(_affected_devices(incident))
    children = _num(_get(incident, "child_count", len(_children(incident))), len(_children(incident)))
    gain = _num(_get(incident, "estimated_score_gain", 0))
    minutes = max(1, _num(_get(incident, "estimated_repair_minutes", 5), 5))
    severity_bonus = {"critical": 35, "warning": 18, "maintenance": 8}.get(_severity(incident), 8)
    effort_bonus = max(0, 12 - min(12, minutes))
    score = severity_bonus + round(entities * 0.35) + round(devices * 1.5) + round(children * 1.8) + gain * 6 + effort_bonus
    return int(max(1, min(100, score)))


def impact_label(score: int) -> str:
    if score >= 85:
        return "Extreme impact"
    if score >= 65:
        return "High impact"
    if score >= 40:
        return "Medium impact"
    if score >= 20:
        return "Low impact"
    return "Minor impact"


def explain_root_cause(incident: Any) -> dict[str, str]:
    root = _root(incident)
    entities = len(_affected_entities(incident))
    devices = len(_affected_devices(incident))
    children = _num(_get(incident, "child_count", len(_children(incident))), len(_children(incident)))
    gain = _num(_get(incident, "estimated_score_gain", 0))
    minutes = _num(_get(incident, "estimated_repair_minutes", 5), 5)
    severity = _severity(incident)
    root_lower = root.lower()

    if "mobile" in root_lower or "app" in root_lower:
        why = "One or more Home Assistant Companion App devices appear offline or have stopped updating."
        verify = "Open the Companion App on the affected devices and confirm that they can reach Home Assistant."
        fix = "Refresh or restart the Companion App, verify network access, and check background update permissions."
    elif "mqtt" in root_lower:
        why = "MQTT is a central message bus. When it is unhealthy, many sensors and integrations can become unavailable at once."
        verify = "Open the MQTT integration and broker logs. Confirm clients are connected and messages are flowing."
        fix = "Restart the MQTT broker, verify credentials, and reconnect affected clients."
    elif "frigate" in root_lower:
        why = "Frigate provides camera and object-detection entities. If it is unavailable, camera-related entities can fail together."
        verify = "Open Frigate and check service status, logs, camera streams and detector health."
        fix = "Restart Frigate, verify camera streams, and check hardware acceleration or detector availability."
    elif "icloud" in root_lower:
        why = "iCloud entities depend on account authentication and cloud availability."
        verify = "Check the iCloud integration for reauthentication prompts or account errors."
        fix = "Reauthenticate iCloud and verify that tracked devices update again."
    else:
        why = f"HADocs detected that several symptoms point back to the same root cause: {root}."
        verify = "Open the related integration or device in Home Assistant and check logs, availability and recent changes."
        fix = "Fix the parent integration or device first, then rescan to confirm child incidents disappear."

    impact = f"This is marked as {severity}. It affects {entities} entities, {devices} devices and has {children} child incidents. Fixing it may improve Health Score by +{gain}."
    return {"why": why, "impact": impact, "verify": verify, "fix": fix, "time": f"Estimated repair time: about {minutes} minutes."}


def build_health_forecast(current_score: int, incidents: list[Any], limit: int = 6) -> list[dict[str, int | str]]:
    score = max(0, min(100, _num(current_score)))
    selected = sorted(list(incidents or []), key=lambda i: (calculate_impact_score(i), _num(_get(i, "estimated_score_gain", 0))), reverse=True)[:limit]
    steps = []
    for incident in selected:
        gain = max(0, _num(_get(incident, "estimated_score_gain", 0)))
        score = min(100, score + gain)
        impact = calculate_impact_score(incident)
        steps.append(ForecastStep(_title(incident), _root(incident), gain, _num(_get(incident, "estimated_repair_minutes", 5), 5), score, impact, impact_label(impact)).as_dict())
    return steps


def apply_intelligence_v014(model: Any, executive: Any, incidents: list[Any]) -> Any:
    current_score = _num(_get(executive, "score", 0))
    forecast = build_health_forecast(current_score, incidents, limit=6)
    enriched = []
    for incident in incidents or []:
        impact = calculate_impact_score(incident)
        enriched.append({"root_cause": _root(incident), "title": _title(incident), "impact_score": impact, "impact_label": impact_label(impact), "explain": explain_root_cause(incident)})

    if isinstance(executive, dict):
        executive["health_forecast"] = forecast
        executive["root_cause_intelligence"] = enriched
        return executive

    try:
        setattr(executive, "health_forecast", forecast)
        setattr(executive, "root_cause_intelligence", enriched)
    except Exception:
        pass
    return executive
