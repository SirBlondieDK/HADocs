import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.hadocs.privacy.redaction import redact_dict


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_manifest(version: str = "0.11.0") -> dict:
    return {
        "generator": "HADocs",
        "version": version,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "privacy": {
            "local_only": True,
            "telemetry": False,
            "cloud_upload": False,
            "ai_calls": False,
        },
        "files": ["manifest.json", "summary.json", "redacted/summary.json"],
    }


def build_summary(model=None, executive=None, incidents=None) -> dict:
    incidents = incidents or []
    return {
        "project": "HADocs",
        "summary_type": "knowledge_export_foundation",
        "health_score": getattr(executive, "score", None),
        "potential_score": getattr(executive, "potential_score", None),
        "main_root_cause": getattr(executive, "main_cause", None),
        "incident_count": len(incidents),
        "root_causes": [
            {
                "root_cause": getattr(incident, "root_cause", ""),
                "severity": getattr(incident, "severity", ""),
                "category": getattr(incident, "category", ""),
                "affected_entities": len(getattr(incident, "affected_entities", [])),
                "affected_devices": len(getattr(incident, "affected_devices", [])),
                "estimated_score_gain": getattr(incident, "estimated_score_gain", 0),
                "estimated_repair_minutes": getattr(incident, "estimated_repair_minutes", 0),
            }
            for incident in incidents[:20]
        ],
    }


def export_knowledge(out: Path, model=None, executive=None, incidents=None, version: str = "0.11.0") -> None:
    knowledge_dir = out / "knowledge"
    summary = build_summary(model=model, executive=executive, incidents=incidents)
    write_json(knowledge_dir / "manifest.json", build_manifest(version=version))
    write_json(knowledge_dir / "summary.json", summary)
    write_json(knowledge_dir / "redacted" / "summary.json", redact_dict(summary))
