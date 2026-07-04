from src.hadocs.analyzers.rules import IGNORED_DOMAINS, IGNORED_ENTITY_PATTERNS, PHYSICAL_DOMAINS, SYSTEM_PLATFORMS

IMPORTANT_DOMAINS = {"light","switch","sensor","binary_sensor","camera","media_player","person","lawn_mower","siren","device_tracker"}
SERVER_WORDS = ["hp_mini","homeassistant","adguard","frigate","jellyfin","nextcloud","proxy","zigbee2mqtt","hadashboard","storage","backup","deco","remote_ui","mosquitto","mqtt"]


def state_for(entity_id: str, idx: dict) -> dict:
    return idx["state_by_entity"].get(entity_id, {})


def entity_area(entity: dict, idx: dict) -> str:
    area_id = entity.get("area_id")
    device_id = entity.get("device_id")
    if not area_id and device_id and device_id in idx["device_by_id"]:
        area_id = idx["device_by_id"][device_id].get("area_id")
    return area_id or "_uden_område"


def area_name(area_id: str, idx: dict) -> str:
    if not area_id or area_id == "_uden_område":
        return "Uden område"
    return idx["area_by_id"].get(area_id, {}).get("name", "Uden område")


def device_name(device: dict) -> str:
    return device.get("name_by_user") or device.get("name") or device.get("id") or "Uden navn"


def friendly_name(entity: dict, idx: dict) -> str:
    st = state_for(entity["entity_id"], idx)
    return st.get("attributes", {}).get("friendly_name") or entity.get("name") or entity["entity_id"]


def is_ignored_entity(entity: dict) -> bool:
    entity_id = entity["entity_id"].lower()
    if entity_id.split(".")[0] in IGNORED_DOMAINS:
        return True
    return any(pattern in entity_id for pattern in IGNORED_ENTITY_PATTERNS)


def is_physical_entity(entity: dict) -> bool:
    if entity["entity_id"].split(".")[0] not in PHYSICAL_DOMAINS:
        return False
    if (entity.get("platform") or "") in SYSTEM_PLATFORMS:
        return False
    return not is_ignored_entity(entity)


def is_dashboard_candidate(entity: dict) -> bool:
    return entity["entity_id"].split(".")[0] in IMPORTANT_DOMAINS and not is_ignored_entity(entity)
