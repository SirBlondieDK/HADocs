def _safe_sort_name(item: dict) -> str:
    return str(item.get("name") or item.get("id") or "").lower()


def build_explorer_data(model, graph=None) -> dict:
    areas = []
    for area in getattr(model, "areas", {}).values():
        areas.append({
            "id": getattr(area, "area_id", "") or getattr(area, "id", ""),
            "name": getattr(area, "name", "Unknown area"),
            "device_count": len(getattr(area, "devices", []) or []),
            "entity_count": len(getattr(area, "entities", []) or []),
        })

    devices = []
    for device in getattr(model, "devices", {}).values():
        devices.append({
            "id": getattr(device, "device_id", "") or getattr(device, "id", ""),
            "name": getattr(device, "name", "Unknown device"),
            "area_id": getattr(device, "area_id", ""),
            "manufacturer": getattr(device, "manufacturer", ""),
            "model": getattr(device, "model", ""),
            "classification": getattr(device, "classification", ""),
            "entity_count": len(getattr(device, "entities", []) or []),
            "is_physical": bool(getattr(device, "is_physical", False)),
            "is_virtual": bool(getattr(device, "is_virtual", False)),
            "is_system": bool(getattr(device, "is_system", False)),
        })

    entities = []
    for entity in getattr(model, "entities", {}).values():
        entities.append({
            "id": getattr(entity, "entity_id", ""),
            "name": getattr(entity, "name", ""),
            "domain": getattr(entity, "domain", ""),
            "state": getattr(entity, "state", ""),
            "area_id": getattr(entity, "area_id", ""),
            "device_id": getattr(entity, "device_id", ""),
            "platform": getattr(entity, "platform", ""),
            "importance": getattr(entity, "importance", ""),
            "is_ignored": bool(getattr(entity, "is_ignored", False)),
        })

    integrations = []
    for integration in getattr(model, "integrations", {}).values():
        integrations.append({
            "id": getattr(integration, "platform", ""),
            "name": getattr(integration, "platform", ""),
            "device_count": len(getattr(integration, "devices", []) or []),
            "entity_count": len(getattr(integration, "entities", []) or []),
        })

    return {
        "areas": sorted(areas, key=_safe_sort_name),
        "devices": sorted(devices, key=_safe_sort_name),
        "entities": sorted(entities, key=_safe_sort_name),
        "integrations": sorted(integrations, key=_safe_sort_name),
        "counts": {
            "areas": len(areas),
            "devices": len(devices),
            "entities": len(entities),
            "integrations": len(integrations),
        },
    }


def build_search_index(explorer_data: dict) -> list[dict]:
    index = []
    for kind in ("areas", "devices", "entities", "integrations"):
        for item in explorer_data.get(kind, []):
            title = item.get("name") or item.get("id")
            index.append({
                "type": kind[:-1],
                "title": title,
                "id": item.get("id", ""),
                "text": " ".join(str(v) for v in item.values() if v is not None),
            })
    return index
