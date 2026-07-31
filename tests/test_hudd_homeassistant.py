from hadocs.hudd.homeassistant import (
    build_device_identity,
    match_device_registry_entry,
    serialize_match,
)


def test_ha_aqara_device_is_enriched_offline():
    entry = {
        "id": "ha-aqara",
        "name": "Motion sensor",
        "manufacturer": "Aqara",
        "model": "RTCGQ11LM",
        "identifiers": [["zha", "00:15:8d:00:00:00:00:01"]],
    }
    result = serialize_match(match_device_registry_entry(entry, platforms={"zha"}))
    assert result["offline"] is True
    assert result["device"]["hudd_id"] == "HUDD-DEV-000001"
    assert result["level"] in {"probable", "exact"}


def test_ha_tuya_zigbee_fields_become_exact_identifiers():
    entry = {
        "id": "ha-tuya",
        "name": "RGB bulb",
        "manufacturer": "_TZ3210_mja6r5ix",
        "model": "TS0505B",
        "identifiers": [["zha", "00:12:4b:00:00:00:00:02"]],
    }
    identity = build_device_identity(entry, platforms={"zha"})
    assert identity["identifiers"]["zigbee_manufacturer"] == "_TZ3210_mja6r5ix"
    assert identity["identifiers"]["zigbee_model"] == "TS0505B"

    result = match_device_registry_entry(entry, platforms={"zha"})
    assert result.device is not None
    assert result.device.hudd_id == "HUDD-DEV-000002"
    assert result.level == "exact"


def test_unknown_ha_device_remains_unknown():
    entry = {
        "id": "ha-unknown",
        "name": "Mystery",
        "manufacturer": "Unknown Example Inc",
        "model": "NOT-IN-HUDD",
    }
    result = match_device_registry_entry(entry)
    assert result.device is None
    assert result.level == "unknown"


def test_builder_attaches_hudd_result_to_device_model():
    from hadocs.collectors.homeassistant import build_indexes
    from hadocs.core.builder import build_model

    data = {
        "states": [],
        "entities": [],
        "areas": [],
        "devices": [
            {
                "id": "device-1",
                "name": "Aqara Motion Sensor",
                "manufacturer": "Aqara",
                "model": "RTCGQ11LM",
                "area_id": None,
            }
        ],
        "config": {},
        "services": [],
        "labels": [],
    }
    model = build_model(data, build_indexes(data))
    assert model.devices["device-1"].hudd["device"]["hudd_id"] == "HUDD-DEV-000001"
    assert model.devices["device-1"].hudd["offline"] is True
