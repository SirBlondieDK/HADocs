from src.hadocs.core.classifiers import classify_device, classify_entity
from src.hadocs.core.models import (
    AreaModel,
    DeviceModel,
    EntityModel,
    InstallationModel,
    IntegrationModel,
)

def build_model(data: dict, idx: dict) -> InstallationModel:
    states_by_entity = idx["state_by_entity"]

    areas: dict[str, AreaModel] = {}
    for area in data["areas"]:
        areas[area["area_id"]] = AreaModel(area_id=area["area_id"], name=area.get("name") or area["area_id"])
    areas["_uden_område"] = AreaModel(area_id="_uden_område", name="Uden område")

    entities: dict[str, EntityModel] = {}
    for ent in data["entities"]:
        entity_id = ent["entity_id"]
        state_obj = states_by_entity.get(entity_id, {})
        attr = state_obj.get("attributes", {})
        platform = ent.get("platform") or "_unknown"
        ignored, physical, importance, reason = classify_entity(entity_id, platform)

        area_id = ent.get("area_id")
        device_id = ent.get("device_id")
        if not area_id and device_id and device_id in idx["device_by_id"]:
            area_id = idx["device_by_id"][device_id].get("area_id")
        area_id = area_id or "_uden_område"

        model = EntityModel(
            entity_id=entity_id,
            name=attr.get("friendly_name") or ent.get("name") or entity_id,
            domain=entity_id.split(".")[0],
            platform=platform,
            state=state_obj.get("state", "unknown"),
            area_id=area_id,
            device_id=device_id,
            is_ignored=ignored,
            is_physical=physical,
            importance=importance,
            rule_reason=reason,
            raw=ent,
        )
        entities[entity_id] = model
        areas.setdefault(area_id, AreaModel(area_id=area_id, name=area_id)).entities.append(model)

    devices: dict[str, DeviceModel] = {}
    for dev in data["devices"]:
        device_id = dev["id"]
        dev_entities = [
            entities[e["entity_id"]]
            for e in idx["entities_by_device"].get(device_id, [])
            if e["entity_id"] in entities
        ]
        domains = {e.domain for e in dev_entities}
        platforms = {e.platform for e in dev_entities}
        classification = classify_device(dev, domains, platforms)

        if classification == "physical" and not any(e.is_physical and not e.is_ignored for e in dev_entities):
            classification = "virtual"

        if classification == "physical":
            important_count = sum(1 for e in dev_entities if e.importance == "important")
            diagnostic_count = sum(1 for e in dev_entities if e.importance in ("diagnostic", "ignored"))
            if important_count == 0 and diagnostic_count >= max(1, len(dev_entities) - 1):
                classification = "virtual"

        area_id = dev.get("area_id") or "_uden_område"
        model = DeviceModel(
            device_id=device_id,
            name=dev.get("name_by_user") or dev.get("name") or device_id,
            area_id=area_id,
            manufacturer=dev.get("manufacturer") or "",
            model=dev.get("model") or "",
            sw_version=dev.get("sw_version") or "",
            hw_version=dev.get("hw_version") or "",
            classification=classification,
            entities=dev_entities,
            raw=dev,
        )
        devices[device_id] = model
        areas.setdefault(area_id, AreaModel(area_id=area_id, name=area_id)).devices.append(model)

    integrations: dict[str, IntegrationModel] = {}
    for entity in entities.values():
        integrations.setdefault(entity.platform, IntegrationModel(platform=entity.platform)).entities.append(entity)

    for device in devices.values():
        for platform in {entity.platform for entity in device.entities}:
            integrations.setdefault(platform, IntegrationModel(platform=platform)).devices.append(device)

    return InstallationModel(
    areas=areas,
    devices=devices,
    entities=entities,
    integrations=integrations,
    config=data.get("config", {}),
    states=data.get("states", []),
    services=data.get("services", []),
    labels=data.get("labels", []),
    raw=data,
)
