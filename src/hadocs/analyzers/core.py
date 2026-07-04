from collections import Counter, defaultdict

from src.hadocs.analyzers.helpers import (
    SERVER_WORDS,
    entity_area,
    is_dashboard_candidate,
    is_ignored_entity,
    is_physical_entity,
    state_for,
)
from src.hadocs.analyzers.rules import CRITICAL_ENTITY_PATTERNS


def analyze(data: dict, idx: dict) -> dict:
    states = data["states"]
    entities = data["entities"]
    devices = data["devices"]
    entity_by_id = {e["entity_id"]: e for e in entities}

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

    out["ignored_entities"] = [e for e in entities if is_ignored_entity(e)]
    out["physical_entities"] = [e for e in entities if is_physical_entity(e)]

    out["real_unavailable"] = []
    out["real_unknown"] = []
    out["ignored_unknown_unavailable"] = []

    for st in states:
        state = st.get("state")
        if state not in ("unknown", "unavailable"):
            continue

        ent = entity_by_id.get(st["entity_id"])
        if not ent:
            continue

        if is_ignored_entity(ent):
            out["ignored_unknown_unavailable"].append(st)
        elif is_physical_entity(ent):
            if state == "unavailable":
                out["real_unavailable"].append(st)
            else:
                out["real_unknown"].append(st)
        else:
            out["ignored_unknown_unavailable"].append(st)

    out["entities_without_area"] = [
        e for e in entities
        if entity_area(e, idx) == "_uden_område" and is_physical_entity(e)
    ]

    out["devices_without_area"] = [
        d for d in devices
        if not d.get("area_id") and _looks_like_physical_device(d)
    ]

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
        if st.get("state") not in ("unavailable", "unknown"):
            continue
        if is_ignored_entity(e):
            continue
        if any(pattern in eid for pattern in CRITICAL_ENTITY_PATTERNS):
            out["offline_critical"].append(e)

    out["unavailable"] = out["real_unavailable"]
    out["unknown"] = out["real_unknown"]

    return out


def _looks_like_physical_device(device: dict) -> bool:
    manufacturer = (device.get("manufacturer") or "").lower()
    model = (device.get("model") or "").lower()
    name = (device.get("name_by_user") or device.get("name") or "").lower()

    system_words = [
        "home assistant",
        "integration",
        "plugin",
        "hacs",
        "backup",
        "conversation",
        "google ai",
        "openai",
        "forecast",
    ]

    blob = " ".join([manufacturer, model, name])
    return not any(w in blob for w in system_words)
