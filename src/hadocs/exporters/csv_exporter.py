import csv
from pathlib import Path
from src.hadocs.analyzers.helpers import area_name, device_name, entity_area, friendly_name, is_ignored_entity, is_physical_entity, state_for


def export_entities_csv(out: Path, data: dict, idx: dict) -> None:
    csv_dir = out / "csv"
    csv_dir.mkdir(exist_ok=True)
    with (csv_dir / "entities.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["entity_id","name","state","domain","area","platform","device","manufacturer","model","is_physical","is_ignored"])
        for ent in sorted(data["entities"], key=lambda e: e["entity_id"]):
            st = state_for(ent["entity_id"], idx)
            dev = idx["device_by_id"].get(ent.get("device_id"), {})
            writer.writerow([ent["entity_id"], friendly_name(ent, idx), st.get("state", "unknown"), ent["entity_id"].split(".")[0], area_name(entity_area(ent, idx), idx), ent.get("platform") or "", device_name(dev) if dev else "", dev.get("manufacturer", "") if dev else "", dev.get("model", "") if dev else "", is_physical_entity(ent), is_ignored_entity(ent)])
