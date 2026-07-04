from collections import Counter, defaultdict

from src.hadocs.analyzers.helpers import (
    SERVER_WORDS,
    entity_area,
    friendly_name,
    is_dashboard_candidate,
    state_for,
)


def analyze(data: dict, idx: dict) -> dict:
    states = data["states"]
    entities = data["entities"]
    devices = data["devices"]

    out = {}

    out["counts"] = {
        "states": len(states),
        "entities": len(entities),
        "devices": len(devices),
        "areas": len(data["areas"]),
        "unknown": sum(1 for s in states if s.get("state") == "unknown"),
        "unavailable": sum(1 for s in states if s.get("state") == "unavailable"),
    }

    out["domain_counts"] = Counter(e["entity_id"].split(".")[0] for e in entities)
    out["platform_counts"] = Counter(e.get("platform") or "_unknown" for e in entities)

    out["unavailable"] = [s for s in states if s.get("state") == "unavailable"]
    out["unknown"] = [s for s in states if s.get("state") == "unknown"]

    out["entities_without_area"] = [
        e for e in entities if entity_area(e, idx) == "_uden_område"
    ]

    out["devices_without_area"] = [d for d in devices if not d.get("area_id")]

    name_counts = Counter()
    for s in states:
        fn = s.get("attributes", {}).get("friendly_name")
        if fn:
            name_counts[fn] += 1
    out["duplicate_names"] = {k: v for k, v in name_counts.items() if v > 1}

    out["dashboard_candidates_by_area"] = defaultdict(list)
    for e in entities:
        if is_dashboard_candidate(e):
            out["dashboard_candidates_by_area"][entity_area(e, idx)].append(e)

    out["server_entities"] = []
    for e in entities:
        eid = e["entity_id"].lower()
        if any(w in eid for w in SERVER_WORDS):
            out["server_entities"].append(e)

    out["battery_entities"] = []
    for e in entities:
        eid = e["entity_id"].lower()
        st = state_for(e["entity_id"], idx)
        attr = st.get("attributes", {})
        dc = attr.get("device_class")
        if "battery" in eid or dc == "battery":
            out["battery_entities"].append(e)

    out["low_batteries"] = []
    for e in out["battery_entities"]:
        st = state_for(e["entity_id"], idx)
        try:
            val = float(st.get("state"))
            if val <= 25:
                out["low_batteries"].append((e, val))
        except Exception:
            pass

    out["offline_critical"] = []
    for e in entities:
        eid = e["entity_id"].lower()
        st = state_for(e["entity_id"], idx)
        if st.get("state") in ("unavailable", "unknown"):
            if any(w in eid for w in ["homeassistant", "adguard", "zigbee2mqtt", "frigate", "remote_ui", "internet_online"]):
                out["offline_critical"].append(e)

    return out
