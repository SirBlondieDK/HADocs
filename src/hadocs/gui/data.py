import json
from pathlib import Path


def safe_read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_latest_summary(output_dir):
    output = Path(output_dir)
    recommendations = safe_read_json(output / "knowledge" / "recommendations.json")
    incidents = safe_read_json(output / "knowledge" / "incidents.json")
    return {
        "health": safe_read_json(output / "knowledge" / "health.json"),
        "inventory": safe_read_json(output / "knowledge" / "inventory.json"),
        "recommendations": recommendations if isinstance(recommendations, list) else [],
        "incidents": incidents if isinstance(incidents, list) else [],
        "latest": safe_read_json(output / "history" / "latest.json"),
        "summary": safe_read_json(output / "history" / "summary.json"),
    }
