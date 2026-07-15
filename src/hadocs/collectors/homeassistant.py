from __future__ import annotations

from collections import defaultdict
from typing import Callable

from src.hadocs.collectors.installation import InstallationCollector
from src.hadocs.providers import HomeAssistantProvider


LogFunction = Callable[[str], None]


def collect_all(
    cfg: dict,
    log: LogFunction = print,
    provider: HomeAssistantProvider | None = None,
) -> dict:
    """Compatibility wrapper for complete Home Assistant collection."""

    provider = provider or HomeAssistantProvider.from_config(cfg)

    return InstallationCollector(
        provider=provider,
        config=cfg,
        log=log,
    ).collect()


def build_indexes(data: dict) -> dict:
    """Build lookup indexes for collected Home Assistant data."""

    idx = {
        "state_by_entity": {
            state["entity_id"]: state
            for state in data["states"]
        },
        "device_by_id": {
            device["id"]: device
            for device in data["devices"]
        },
        "area_by_id": {
            area["area_id"]: area
            for area in data["areas"]
        },
    }

    by_area = defaultdict(list)
    by_device = defaultdict(list)
    by_domain = defaultdict(list)
    by_platform = defaultdict(list)

    for entity in data["entities"]:
        entity_id = entity["entity_id"]
        domain = entity_id.split(".", maxsplit=1)[0]

        by_domain[domain].append(entity)

        platform = entity.get("platform") or "_unknown"
        by_platform[platform].append(entity)

        device_id = entity.get("device_id")
        if device_id:
            by_device[device_id].append(entity)

        area_id = entity.get("area_id")

        if (
            not area_id
            and device_id
            and device_id in idx["device_by_id"]
        ):
            area_id = idx["device_by_id"][device_id].get("area_id")

        by_area[area_id or "_uden_område"].append(entity)

    idx["entities_by_area"] = by_area
    idx["entities_by_device"] = by_device
    idx["entities_by_domain"] = by_domain
    idx["entities_by_platform"] = by_platform

    return idx