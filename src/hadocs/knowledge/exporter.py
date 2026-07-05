import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.hadocs.explain.engine import explain_incident
from src.hadocs.privacy.redaction import redact_dict, redact_value


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_manifest(version: str = "0.12.0") -> dict:
    return {
        "generator": "HADocs",
        "version": version,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "privacy": {
            "local_only": True,
            "telemetry": False,
            "cloud_upload": False,
            "ai_calls": False,
            "ai_compatible": True,
            "ai_connected": False,
        },
        "files": [
            "manifest.json",
            "inventory.json",
            "health.json",
            "incidents.json",
            "recommendations.json",
            "relationships.json",
            "summary.md",
            "redacted/manifest.json",
            "redacted/inventory.json",
            "redacted/health.json",
            "redacted/incidents.json",
            "redacted/recommendations.json",
            "redacted/relationships.json",
            "redacted/summary.md",
        ],
    }


def build_inventory(model) -> dict:
    if model is None:
        return {"areas": 0, "devices": 0, "entities": 0, "integrations": 0}

    physical = [d for d in model.devices.values() if d.is_physical]
    virtual = [d for d in model.devices.values() if d.is_virtual]
    system = [d for d in model.devices.values() if d.is_system]

    return {
        "areas": len(model.areas),
        "devices": len(model.devices),
        "physical_devices": len(physical),
        "virtual_devices": len(virtual),
        "system_devices": len(system),
        "entities": len(model.entities),
        "integrations": len(model.integrations),
    }


def build_health(executive) -> dict:
    return {
        "health_score": getattr(executive, "score", None),
        "status": getattr(executive, "status", None),
        "potential_score": getattr(executive, "potential_score", None),
        "estimated_repair_minutes": getattr(executive, "estimated_repair_minutes", None),
        "main_root_cause": getattr(executive, "main_cause", None),
    }


def build_incidents(incidents) -> list[dict]:
    return [
        {
            "incident_id": getattr(incident, "incident_id", ""),
            "title": getattr(incident, "title", ""),
            "category": getattr(incident, "category", ""),
            "severity": getattr(incident, "severity", ""),
            "root_cause": getattr(incident, "root_cause", ""),
            "affected_entities": getattr(incident, "affected_entities", []),
            "affected_devices": getattr(incident, "affected_devices", []),
            "affected_integrations": getattr(incident, "affected_integrations", []),
            "child_incident_count": getattr(incident, "child_count", 0),
            "estimated_score_gain": getattr(incident, "estimated_score_gain", 0),
            "estimated_repair_minutes": getattr(incident, "estimated_repair_minutes", 0),
            "recommendation": getattr(incident, "recommendation", ""),
            "explanation": explain_incident(incident),
        }
        for incident in (incidents or [])
    ]


def build_recommendations(executive) -> list[dict]:
    actions = getattr(executive, "actions", []) or []
    return [
        {
            "title": getattr(action, "title", ""),
            "priority": getattr(action, "priority", 0),
            "reason": getattr(action, "reason", ""),
            "estimated_score_gain": getattr(action, "estimated_score_gain", 0),
            "estimated_repair_minutes": getattr(action, "estimated_repair_minutes", 0),
            "related_items": getattr(action, "related_items", []),
        }
        for action in actions
    ]


def _safe_len(value) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def _safe_items(value):
    if isinstance(value, dict):
        return value.items()
    if isinstance(value, list):
        return enumerate(value)
    return []


def build_relationships(graph) -> dict:
    if graph is None:
        return {"entities": 0, "devices": 0, "integrations": 0}

    entities = getattr(graph, "entities", {})
    devices = getattr(graph, "devices", {})
    integrations = getattr(graph, "integrations", {})

    return {
        "entities": _safe_len(entities),
        "devices": _safe_len(devices),
        "integrations": _safe_len(integrations),
        "entity_ids": [
            str(key)
            for key, _value in list(_safe_items(entities))[:500]
        ],
        "device_ids": [
            str(key)
            for key, _value in list(_safe_items(devices))[:500]
        ],
        "integration_ids": [
            str(key)
            for key, _value in list(_safe_items(integrations))[:500]
        ],
    }

def build_summary_markdown(inventory: dict, health: dict, incidents: list[dict]) -> str:
    lines = [
        "# HADocs Knowledge Summary",
        "",
        "This file is generated locally by HADocs.",
        "",
        "## Privacy",
        "",
        "- Local only: yes",
        "- Telemetry: no",
        "- Cloud upload: no",
        "- AI calls: no",
        "",
        "## Health",
        "",
        f"- Health score: `{health.get('health_score')}`",
        f"- Status: `{health.get('status')}`",
        f"- Potential score: `{health.get('potential_score')}`",
        f"- Main root cause: `{health.get('main_root_cause')}`",
        "",
        "## Inventory",
        "",
        f"- Areas: `{inventory.get('areas')}`",
        f"- Devices: `{inventory.get('devices')}`",
        f"- Entities: `{inventory.get('entities')}`",
        f"- Integrations: `{inventory.get('integrations')}`",
        "",
        "## Top root causes",
        "",
    ]

    for incident in incidents[:10]:
        lines.append(f"- **{incident.get('root_cause')}** — {len(incident.get('affected_entities', []))} affected entities")

    return "\n".join(lines) + "\n"

def build_summary(
    inventory: dict | None = None,
    health: dict | None = None,
    incidents: list[dict] | None = None,
) -> dict:
    inventory = inventory or {}
    health = health or {}
    incidents = incidents or []

    return {
        "project": "HADocs",
        "summary_type": "knowledge_export",
        "inventory": inventory,
        "health": health,
        "incident_count": len(incidents),
        "root_causes": [
            {
                "root_cause": incident.get("root_cause", ""),
                "severity": incident.get("severity", ""),
                "category": incident.get("category", ""),
                "affected_entities": len(incident.get("affected_entities", [])),
                "affected_devices": len(incident.get("affected_devices", [])),
                "estimated_score_gain": incident.get("estimated_score_gain", 0),
                "estimated_repair_minutes": incident.get("estimated_repair_minutes", 0),
            }
            for incident in incidents[:20]
        ],
    }

def export_knowledge(out: Path, model=None, executive=None, incidents=None, graph=None, version: str = "0.12.0") -> None:
    knowledge_dir = out / "knowledge"
    redacted_dir = knowledge_dir / "redacted"

    manifest = build_manifest(version=version)
    inventory = build_inventory(model)
    health = build_health(executive)
    incident_data = build_incidents(incidents)
    recommendations = build_recommendations(executive)
    relationships = build_relationships(graph)
    summary_md = build_summary_markdown(inventory, health, incident_data)

    payloads = {
        "manifest.json": manifest,
        "inventory.json": inventory,
        "health.json": health,
        "incidents.json": incident_data,
        "recommendations.json": recommendations,
        "relationships.json": relationships,
    }

    for filename, payload in payloads.items():
        write_json(knowledge_dir / filename, payload)
        write_json(redacted_dir / filename, redact_value(payload))

    write_text(knowledge_dir / "summary.md", summary_md)
    write_text(redacted_dir / "summary.md", redact_dict({"summary": summary_md})["summary"])
