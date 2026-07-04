from collections import Counter, defaultdict
from src.hadocs.analyzers.helpers import SERVER_WORDS, entity_area, is_dashboard_candidate, is_ignored_entity, is_physical_entity, state_for
from src.hadocs.analyzers.rules import CRITICAL_ENTITY_PATTERNS


def analyze(data: dict, idx: dict) -> dict:
    states, entities, devices = data["states"], data["entities"], data["devices"]
    entity_by_id = {e["entity_id"]: e for e in entities}
    out = {
        "counts": {
            "states": len(states), "entities": len(entities), "devices": len(devices), "areas": len(data["areas"]),
            "unknown": sum(1 for s in states if s.get("state") == "unknown"),
            "unavailable": sum(1 for s in states if s.get("state") == "unavailable"),
        },
        "domain_counts": Counter(e["entity_id"].split(".")[0] for e in entities),
        "platform_counts": Counter(e.get("platform") or "_unknown" for e in entities),
        "ignored_entities": [e for e in entities if is_ignored_entity(e)],
        "physical_entities": [e for e in entities if is_physical_entity(e)],
        "real_unavailable": [], "real_unknown": [], "ignored_unknown_unavailable": [],
    }
    for st in states:
        if st.get("state") not in ("unknown", "unavailable"):
            continue
        ent = entity_by_id.get(st["entity_id"])
        if not ent:
            continue
        if is_ignored_entity(ent) or not is_physical_entity(ent):
            out["ignored_unknown_unavailable"].append(st)
        elif st.get("state") == "unavailable":
            out["real_unavailable"].append(st)
        else:
            out["real_unknown"].append(st)
    out["entities_without_area"] = [e for e in entities if entity_area(e, idx) == "_uden_område" and is_physical_entity(e)]
    out["devices_without_area"] = [d for d in devices if not d.get("area_id") and _looks_like_physical_device(d)]
    name_counts = Counter(s.get("attributes", {}).get("friendly_name") for s in states if s.get("attributes", {}).get("friendly_name"))
    out["duplicate_names"] = {k: v for k, v in name_counts.items() if v > 1}
    out["dashboard_candidates_by_area"] = defaultdict(list)
    for e in entities:
        if is_dashboard_candidate(e):
            out["dashboard_candidates_by_area"][entity_area(e, idx)].append(e)
    out["server_entities"] = [e for e in entities if any(w in e["entity_id"].lower() for w in SERVER_WORDS)]
    out["battery_entities"] = []
    for e in entities:
        st = state_for(e["entity_id"], idx)
        if "battery" in e["entity_id"].lower() or st.get("attributes", {}).get("device_class") == "battery":
            out["battery_entities"].append(e)
    out["low_batteries"] = []
    for e in out["battery_entities"]:
        try:
            val = float(state_for(e["entity_id"], idx).get("state"))
            if val <= 25:
                out["low_batteries"].append((e, val))
        except Exception:
            pass
    out["offline_critical"] = []
    for e in entities:
        st = state_for(e["entity_id"], idx)
        if st.get("state") in ("unavailable", "unknown") and not is_ignored_entity(e):
            if any(pattern in e["entity_id"].lower() for pattern in CRITICAL_ENTITY_PATTERNS):
                out["offline_critical"].append(e)
    out["unavailable"] = out["real_unavailable"]
    out["unknown"] = out["real_unknown"]
    return out


def _looks_like_physical_device(device: dict) -> bool:
    blob = " ".join([(device.get("manufacturer") or ""), (device.get("model") or ""), (device.get("name_by_user") or device.get("name") or "")]).lower()
    system_words = ["home assistant", "integration", "plugin", "hacs", "backup", "conversation", "google ai", "openai", "forecast"]
    return not any(w in blob for w in system_words)
