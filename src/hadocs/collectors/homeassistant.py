import json
from pathlib import Path
from collections import defaultdict
from src.hadocs.api.client import HomeAssistantAPI


def collect_all(cfg: dict, log=print) -> dict:
    api = HomeAssistantAPI(cfg["ha_url"], cfg["token"])
    cache = Path(cfg.get("cache_dir", "cache"))
    cache.mkdir(exist_ok=True)
    data = {}
    for name, endpoint in {"states":"/api/states", "config":"/api/config", "services":"/api/services"}.items():
        log(f"Henter {name}...")
        data[name] = api.rest_get(endpoint)
    for name, msg_type in {"entities":"config/entity_registry/list", "devices":"config/device_registry/list", "areas":"config/area_registry/list"}.items():
        log(f"Henter {name}...")
        data[name] = api.ws_call(msg_type)
    data["labels"] = []
    try:
        log("Henter labels...")
        data["labels"] = api.ws_call("config/label_registry/list")
    except Exception as exc:
        log(f"Labels sprunget over: {exc}")
    for name, value in data.items():
        (cache / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def build_indexes(data: dict) -> dict:
    idx = {
        "state_by_entity": {s["entity_id"]: s for s in data["states"]},
        "device_by_id": {d["id"]: d for d in data["devices"]},
        "area_by_id": {a["area_id"]: a for a in data["areas"]},
    }
    by_area, by_device, by_domain, by_platform = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for ent in data["entities"]:
        entity_id = ent["entity_id"]
        by_domain[entity_id.split(".")[0]].append(ent)
        by_platform[ent.get("platform") or "_unknown"].append(ent)
        device_id = ent.get("device_id")
        if device_id:
            by_device[device_id].append(ent)
        area_id = ent.get("area_id")
        if not area_id and device_id and device_id in idx["device_by_id"]:
            area_id = idx["device_by_id"][device_id].get("area_id")
        by_area[area_id or "_uden_område"].append(ent)
    idx.update({"entities_by_area":by_area,"entities_by_device":by_device,"entities_by_domain":by_domain,"entities_by_platform":by_platform})
    return idx
