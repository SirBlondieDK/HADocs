from collections import Counter, defaultdict


IMPORTANT_DOMAINS = {
    "light", "switch", "sensor", "binary_sensor", "camera",
    "media_player", "person", "lawn_mower", "siren", "device_tracker"
}

NOISY_ENTITY_WORDS = [
    "favorite_current_song",
    "do_not_disturb",
    "power_on_behavior",
    "color_power_on_behavior",
    "last_seen",
    "linkquality",
    "pre_release",
    "_update",
    "create_snapshot",
]

SERVER_WORDS = [
    "hp_mini", "homeassistant", "adguard", "frigate", "jellyfin",
    "nextcloud", "proxy", "zigbee2mqtt", "hadashboard", "storage",
    "backup", "deco", "remote_ui", "mosquitto", "mqtt",
]


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
    attr = st.get("attributes", {})
    return attr.get("friendly_name") or entity.get("name") or entity["entity_id"]


def is_noisy(entity_id: str) -> bool:
    low = entity_id.lower()
    return any(w in low for w in NOISY_ENTITY_WORDS)


def is_dashboard_candidate(entity: dict) -> bool:
    entity_id = entity["entity_id"]
    domain = entity_id.split(".")[0]
    return domain in IMPORTANT_DOMAINS and not is_noisy(entity_id)
