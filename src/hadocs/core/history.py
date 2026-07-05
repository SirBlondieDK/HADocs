import json
from datetime import datetime
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA_VERSION = 2


def _history_dir(cfg: dict) -> Path:
    output = Path(cfg.get("output_dir", "output"))
    return output / ".hadocs_history"


def _public_history_dir(cfg: dict) -> Path:
    output = Path(cfg.get("output_dir", "output"))
    return output / "history"


def _problem_entities(model) -> list:
    return [
        e for e in model.entities.values()
        if e.state in ("unknown", "unavailable")
        and not e.is_ignored
        and e.importance != "diagnostic"
    ]


def _root_cause_key(incident) -> str:
    return str(getattr(incident, "root_cause", "") or getattr(incident, "title", "") or "unknown")


def save_history_snapshot(cfg: dict, model, score: int, executive, incidents=None, raw_incidents=None) -> Path:
    """Save a history snapshot for the current scan.

    The private history folder is kept as `.hadocs_history` to avoid cluttering
    the report root, while a public `history/latest.json` is exported for the
    HTML dashboard and future Explorer pages.
    """
    history_dir = _history_dir(cfg)
    history_dir.mkdir(parents=True, exist_ok=True)

    public_dir = _public_history_dir(cfg)
    public_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    iso_timestamp = datetime.now().isoformat(timespec="seconds")
    path = history_dir / f"{timestamp}.json"

    incidents = incidents or []
    raw_incidents = raw_incidents or []
    physical_devices = [d for d in model.devices.values() if d.is_physical]
    problem_entities = _problem_entities(model)

    data = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "timestamp": timestamp,
        "generated_at": iso_timestamp,
        "health_score": score,
        "status": executive.status,
        "potential_score": executive.potential_score,
        "estimated_repair_minutes": executive.estimated_repair_minutes,
        "main_root_cause": executive.main_cause,
        "areas": len(model.areas),
        "physical_devices": len(physical_devices),
        "devices": len(model.devices),
        "entities": len(model.entities),
        "integrations": len(model.integrations),
        "problem_entities": len(problem_entities),
        "critical_actions": executive.critical_count,
        "warning_actions": executive.warning_count,
        "maintenance_actions": executive.maintenance_count,
        "collapsed_incidents": len(incidents),
        "raw_incidents": len(raw_incidents),
        "root_causes": [
            {
                "key": _root_cause_key(incident),
                "title": getattr(incident, "title", ""),
                "severity": getattr(incident, "severity", ""),
                "category": getattr(incident, "category", ""),
                "affected_entities": len(getattr(incident, "affected_entities", []) or []),
                "affected_devices": len(getattr(incident, "affected_devices", []) or []),
                "estimated_score_gain": getattr(incident, "estimated_score_gain", 0),
                "estimated_repair_minutes": getattr(incident, "estimated_repair_minutes", 0),
            }
            for incident in incidents[:25]
        ],
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    (public_dir / "latest.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_history(cfg: dict) -> list[dict]:
    history_dir = _history_dir(cfg)
    if not history_dir.exists():
        return []

    snapshots = []
    for file in sorted(history_dir.glob("*.json")):
        try:
            snapshots.append(json.loads(file.read_text(encoding="utf-8")))
        except Exception:
            continue

    return snapshots


def compare_last_two(cfg: dict) -> dict | None:
    history = load_history(cfg)
    if len(history) < 2:
        return None

    previous = history[-2]
    current = history[-1]
    return compare_snapshots(previous, current)


def compare_snapshots(previous: dict, current: dict) -> dict:
    previous_causes = {item.get("key") for item in previous.get("root_causes", [])}
    current_causes = {item.get("key") for item in current.get("root_causes", [])}

    return {
        "previous": previous,
        "current": current,
        "health_delta": current.get("health_score", 0) - previous.get("health_score", 0),
        "potential_delta": current.get("potential_score", 0) - previous.get("potential_score", 0),
        "problem_entity_delta": current.get("problem_entities", 0) - previous.get("problem_entities", 0),
        "critical_delta": current.get("critical_actions", 0) - previous.get("critical_actions", 0),
        "warning_delta": current.get("warning_actions", 0) - previous.get("warning_actions", 0),
        "maintenance_delta": current.get("maintenance_actions", 0) - previous.get("maintenance_actions", 0),
        "new_root_causes": sorted(c for c in current_causes - previous_causes if c),
        "resolved_root_causes": sorted(c for c in previous_causes - current_causes if c),
    }


def build_trend_summary(history: list[dict]) -> dict:
    if not history:
        return {
            "scan_count": 0,
            "health_points": [],
            "problem_entity_points": [],
            "latest": None,
            "best_health": None,
            "worst_health": None,
            "health_change_total": 0,
        }

    health_points = [
        {
            "timestamp": item.get("timestamp", ""),
            "generated_at": item.get("generated_at", ""),
            "value": item.get("health_score", 0),
        }
        for item in history
    ]
    problem_points = [
        {
            "timestamp": item.get("timestamp", ""),
            "generated_at": item.get("generated_at", ""),
            "value": item.get("problem_entities", 0),
        }
        for item in history
    ]
    scores = [p["value"] for p in health_points]

    return {
        "scan_count": len(history),
        "health_points": health_points,
        "problem_entity_points": problem_points,
        "latest": history[-1],
        "best_health": max(scores),
        "worst_health": min(scores),
        "health_change_total": scores[-1] - scores[0] if len(scores) > 1 else 0,
    }


def sparkline(values: list[int], width: int = 24) -> str:
    """Return a compact unicode sparkline for markdown reports."""
    if not values:
        return ""
    ticks = "▁▂▃▄▅▆▇█"
    if len(values) > width:
        step = max(1, round(len(values) / width))
        values = values[::step][-width:]
    low = min(values)
    high = max(values)
    if low == high:
        return ticks[0] * len(values)
    return "".join(ticks[round((value - low) / (high - low) * (len(ticks) - 1))] for value in values)


def export_history_summary(cfg: dict) -> Path:
    history = load_history(cfg)
    summary = build_trend_summary(history)
    public_dir = _public_history_dir(cfg)
    public_dir.mkdir(parents=True, exist_ok=True)
    path = public_dir / "summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path
