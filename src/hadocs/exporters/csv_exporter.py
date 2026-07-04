import csv
from pathlib import Path

from src.hadocs.core.models import HADocsModel


def export_entities_csv(out: Path, model: HADocsModel) -> None:
    csv_dir = out / "csv"
    csv_dir.mkdir(exist_ok=True)

    with (csv_dir / "entities.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "entity_id", "name", "state", "domain", "area_id", "platform",
            "device_id", "is_physical", "is_ignored", "importance", "rule_reason"
        ])

        for entity in sorted(model.entities.values(), key=lambda e: e.entity_id):
            writer.writerow([
                entity.entity_id, entity.name, entity.state, entity.domain,
                entity.area_id, entity.platform, entity.device_id or "",
                entity.is_physical, entity.is_ignored, entity.importance, entity.rule_reason,
            ])


def export_devices_csv(out: Path, model: HADocsModel) -> None:
    csv_dir = out / "csv"
    csv_dir.mkdir(exist_ok=True)

    with (csv_dir / "devices.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["device_id", "name", "area_id", "manufacturer", "model", "classification", "entity_count"])

        for device in sorted(model.devices.values(), key=lambda d: d.name):
            writer.writerow([
                device.device_id, device.name, device.area_id, device.manufacturer,
                device.model, device.classification, len(device.entities),
            ])
