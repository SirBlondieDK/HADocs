import json
from datetime import datetime
from pathlib import Path


def _history_dir(cfg: dict) -> Path:
    output = Path(cfg.get("output_dir", "output"))
    return output / ".hadocs_history"


def save_history_snapshot(cfg: dict, model, score: int, executive) -> Path:
    history_dir = _history_dir(cfg)
    history_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = history_dir / f"{timestamp}.json"

    physical_devices = [d for d in model.devices.values() if d.is_physical]
    problem_entities = [
        e for e in model.entities.values()
        if e.state in ("unknown", "unavailable")
        and not e.is_ignored
        and e.importance != "diagnostic"
    ]

    data = {
        "timestamp": timestamp,
        "health_score": score,
        "status": executive.status,
        "potential_score": executive.potential_score,
        "physical_devices": len(physical_devices),
        "entities": len(model.entities),
        "integrations": len(model.integrations),
        "problem_entities": len(problem_entities),
        "critical_actions": executive.critical_count,
        "warning_actions": executive.warning_count,
        "maintenance_actions": executive.maintenance_count,
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
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

    return {
        "previous": previous,
        "current": current,
        "health_delta": current.get("health_score", 0) - previous.get("health_score", 0),
        "problem_entity_delta": current.get("problem_entities", 0) - previous.get("problem_entities", 0),
        "critical_delta": current.get("critical_actions", 0) - previous.get("critical_actions", 0),
        "warning_delta": current.get("warning_actions", 0) - previous.get("warning_actions", 0),
    }
