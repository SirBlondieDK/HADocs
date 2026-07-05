from src.hadocs.core.health import find_duplicate_names_by_domain
from src.hadocs.core.models import DeviceHealth, HADocsModel


def build_recommendations(model: HADocsModel, device_health: list[DeviceHealth]) -> list[dict]:
    recommendations = []

    for item in sorted([d for d in device_health if d.status == "problem"], key=lambda d: d.score):
        recommendations.append({
            "priority": 5,
            "title": f"Fix device: {item.device.name}",
            "reason": "; ".join(item.reasons) or "Device has serious health issues.",
            "estimated_score_gain": 5,
        })

    for item in sorted([d for d in device_health if d.status == "warning"], key=lambda d: d.score):
        recommendations.append({
            "priority": 4,
            "title": f"Check device: {item.device.name}",
            "reason": "; ".join(item.reasons) or "Device has warnings.",
            "estimated_score_gain": 2,
        })

    without_area = [
        d for d in model.devices.values()
        if d.is_physical and (not d.area_id or d.area_id == "_uden_område")
    ]
    if without_area:
        recommendations.append({
            "priority": 3,
            "title": f"Assign {len(without_area)} physical devices to areas",
            "reason": "Physical devices without areas are harder to document, analyze, and place on dashboards.",
            "estimated_score_gain": min(6, max(1, len(without_area) // 10)),
        })

    duplicates = find_duplicate_names_by_domain(model)
    if duplicates:
        recommendations.append({
            "priority": 2,
            "title": f"Review {len(duplicates)} duplicate names within the same domain",
            "reason": "Duplicate names can make dashboards, automations, and documentation harder to understand.",
            "estimated_score_gain": min(2, max(1, len(duplicates) // 15)),
        })

    return sorted(recommendations, key=lambda r: (-r["priority"], -r["estimated_score_gain"]))
