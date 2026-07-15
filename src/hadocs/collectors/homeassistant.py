from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Callable

from src.hadocs.providers import HomeAssistantProvider


LogFunction = Callable[[str], None]


def collect_all(
    cfg: dict,
    log: LogFunction = print,
    provider: HomeAssistantProvider | None = None,
) -> dict:
    """Collect all supported Home Assistant data."""

    provider = provider or HomeAssistantProvider.from_config(cfg)

    save_raw_cache = bool(cfg.get("save_raw_cache", False))
    cache = Path(cfg.get("cache_dir", "cache"))

    if save_raw_cache:
        cache.mkdir(parents=True, exist_ok=True)
        log(
            "WARNING: Raw Home Assistant API responses will be written to disk. "
            "These files may contain sensitive information."
        )

    data = {}

    rest_collectors = {
        "states": provider.get_states,
        "config": provider.get_config,
        "services": provider.get_services,
    }

    for name, collector in rest_collectors.items():
        log(f"Collecting {name}...")
        data[name] = collector()

    websocket_collectors = {
        "entities": provider.get_entities,
        "devices": provider.get_devices,
        "areas": provider.get_areas,
    }

    for name, collector in websocket_collectors.items():
        log(f"Collecting {name}...")
        data[name] = collector()

    data["labels"] = []

    try:
        log("Collecting labels...")
        data["labels"] = provider.get_labels()
    except Exception as exc:
        log(f"Labels skipped: {exc}")

    if save_raw_cache:
        for name, value in data.items():
            (cache / f"{name}.json").write_text(
                json.dumps(value, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    return data


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
