def _safe_sort_name(item: dict) -> str:
    return str(item.get("name") or item.get("id") or "").lower()


def _friendly_platform(platform: str) -> str:
    """Return a compact human-readable integration label."""
    aliases = {
        "zha": "ZHA",
        "mqtt": "MQTT",
        "wled": "WLED",
        "esphome": "ESPHome",
        "hue": "Philips Hue",
        "mobile_app": "Mobile App",
        "google_cast": "Google Cast",
        "homekit_controller": "HomeKit Device",
        "matter": "Matter",
        "zwave_js": "Z-Wave JS",
        "ibeacon": "iBeacon",
    }
    value = str(platform or "").strip()
    if not value:
        return ""
    return aliases.get(value.casefold(), value.replace("_", " ").title())


def build_explorer_data(model, graph=None) -> dict:
    area_names = {
        str(getattr(area, "area_id", "") or getattr(area, "id", "")): str(
            getattr(area, "name", "Unknown area")
        )
        for area in getattr(model, "areas", {}).values()
    }

    areas = []
    for area in getattr(model, "areas", {}).values():
        area_id = getattr(area, "area_id", "") or getattr(area, "id", "")
        areas.append({
            "id": area_id,
            "name": getattr(area, "name", "Unknown area"),
            "device_count": len(getattr(area, "devices", []) or []),
            "entity_count": len(getattr(area, "entities", []) or []),
        })

    devices = []
    for device in getattr(model, "devices", {}).values():
        entities_for_device = list(getattr(device, "entities", []) or [])
        platforms = sorted({
            str(getattr(entity, "platform", "") or "").strip()
            for entity in entities_for_device
            if str(getattr(entity, "platform", "") or "").strip()
        })
        domains = sorted({
            str(getattr(entity, "domain", "") or "").strip()
            for entity in entities_for_device
            if str(getattr(entity, "domain", "") or "").strip()
        })
        entity_ids = [
            str(getattr(entity, "entity_id", "") or "").strip()
            for entity in entities_for_device
            if str(getattr(entity, "entity_id", "") or "").strip()
        ]
        states = [
            str(getattr(entity, "state", "") or "").strip().casefold()
            for entity in entities_for_device
        ]
        unavailable_count = sum(state == "unavailable" for state in states)
        unknown_count = sum(state == "unknown" for state in states)
        area_id = str(getattr(device, "area_id", "") or "")
        primary_platform = platforms[0] if platforms else ""

        devices.append({
            "id": getattr(device, "device_id", "") or getattr(device, "id", ""),
            "name": getattr(device, "name", "Unknown device"),
            "area_id": area_id,
            "area_name": area_names.get(area_id, ""),
            "manufacturer": getattr(device, "manufacturer", ""),
            "model": getattr(device, "model", ""),
            "classification": getattr(device, "classification", ""),
            "entity_count": len(entities_for_device),
            "entity_ids": entity_ids,
            "domains": domains,
            "primary_domain": domains[0] if domains else "",
            "platform": primary_platform,
            "integration": _friendly_platform(primary_platform),
            "platforms": platforms,
            "unavailable_count": unavailable_count,
            "unknown_count": unknown_count,
            "online": bool(entities_for_device) and unavailable_count < len(entities_for_device),
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
            "integration": _friendly_platform(getattr(entity, "platform", "")),
            "importance": getattr(entity, "importance", ""),
            "is_ignored": bool(getattr(entity, "is_ignored", False)),
        })

    integrations = []
    for integration in getattr(model, "integrations", {}).values():
        platform = getattr(integration, "platform", "")
        integrations.append({
            "id": platform,
            "name": _friendly_platform(platform) or platform,
            "platform": platform,
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
    """Build a search index while retaining structured Explorer metadata."""
    index = []
    for kind in ("areas", "devices", "entities", "integrations"):
        for item in explorer_data.get(kind, []):
            title = item.get("name") or item.get("id")
            entry = dict(item)
            entry.update({
                "type": kind[:-1],
                "title": title,
                "id": item.get("id", ""),
                "text": " ".join(str(v) for v in item.values() if v is not None),
            })
            index.append(entry)
    return index
