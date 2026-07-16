from __future__ import annotations

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
        area_id = area["area_id"]
        areas[area_id] = AreaModel(
            area_id=area_id,
            name=area.get("name") or area_id,
        )

    areas["_uden_område"] = AreaModel(
        area_id="_uden_område",
        name="Uden område",
    )

    entities: dict[str, EntityModel] = {}
    for ent in data["entities"]:
        entity_id = ent["entity_id"]
        state_obj = states_by_entity.get(entity_id, {})
        attributes = state_obj.get("attributes", {})
        platform = ent.get("platform") or "_unknown"

        ignored, physical, importance, reason = classify_entity(
            entity_id,
            platform,
        )

        area_id = ent.get("area_id")
        device_id = ent.get("device_id")

        if (
            not area_id
            and device_id
            and device_id in idx["device_by_id"]
        ):
            area_id = idx["device_by_id"][device_id].get("area_id")

        area_id = area_id or "_uden_område"

        model = EntityModel(
            entity_id=entity_id,
            name=(
                attributes.get("friendly_name")
                or ent.get("name")
                or entity_id
            ),
            domain=entity_id.split(".", maxsplit=1)[0],
            platform=platform,
            state=state_obj.get("state", "unknown"),
            area_id=area_id,
            device_id=device_id,
            is_ignored=ignored,
            is_physical=physical,
            importance=importance,
            rule_reason=reason,
            attributes=(
                dict(attributes)
                if isinstance(attributes, dict)
                else {}
            ),
            last_changed=state_obj.get("last_changed"),
            last_updated=state_obj.get("last_updated"),
            last_reported=state_obj.get("last_reported"),
            registry=(
                dict(ent)
                if isinstance(ent, dict)
                else {}
            ),
            state_raw=(
                dict(state_obj)
                if isinstance(state_obj, dict)
                else {}
            ),
            raw=(
                dict(ent)
                if isinstance(ent, dict)
                else {}
            ),
        )

        entities[entity_id] = model
        areas.setdefault(
            area_id,
            AreaModel(area_id=area_id, name=area_id),
        ).entities.append(model)

    devices: dict[str, DeviceModel] = {}
    for dev in data["devices"]:
        device_id = dev["id"]

        dev_entities = [
            entities[entity["entity_id"]]
            for entity in idx["entities_by_device"].get(device_id, [])
            if entity["entity_id"] in entities
        ]

        domains = {entity.domain for entity in dev_entities}
        platforms = {entity.platform for entity in dev_entities}
        classification = classify_device(
            dev,
            domains,
            platforms,
        )

        if (
            classification == "physical"
            and not any(
                entity.is_physical and not entity.is_ignored
                for entity in dev_entities
            )
        ):
            classification = "virtual"

        if classification == "physical":
            important_count = sum(
                1
                for entity in dev_entities
                if entity.importance == "important"
            )
            diagnostic_count = sum(
                1
                for entity in dev_entities
                if entity.importance in {"diagnostic", "ignored"}
            )

            if (
                important_count == 0
                and diagnostic_count
                >= max(1, len(dev_entities) - 1)
            ):
                classification = "virtual"

        area_id = dev.get("area_id") or "_uden_område"

        model = DeviceModel(
            device_id=device_id,
            name=(
                dev.get("name_by_user")
                or dev.get("name")
                or device_id
            ),
            area_id=area_id,
            manufacturer=dev.get("manufacturer") or "",
            model=dev.get("model") or "",
            sw_version=dev.get("sw_version") or "",
            hw_version=dev.get("hw_version") or "",
            classification=classification,
            entities=dev_entities,
            raw=(
                dict(dev)
                if isinstance(dev, dict)
                else {}
            ),
        )

        devices[device_id] = model
        areas.setdefault(
            area_id,
            AreaModel(area_id=area_id, name=area_id),
        ).devices.append(model)

    integrations: dict[str, IntegrationModel] = {}

    for entity in entities.values():
        integrations.setdefault(
            entity.platform,
            IntegrationModel(platform=entity.platform),
        ).entities.append(entity)

    for device in devices.values():
        for platform in {
            entity.platform
            for entity in device.entities
        }:
            integrations.setdefault(
                platform,
                IntegrationModel(platform=platform),
            ).devices.append(device)

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
