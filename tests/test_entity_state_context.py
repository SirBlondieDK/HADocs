from src.hadocs.core.builder import build_model


def test_builder_preserves_entity_state_context():
    entity_registry = {
        "entity_id": "sensor.kitchen_temperature",
        "platform": "zha",
        "device_id": "device-1",
        "area_id": "kitchen",
        "disabled_by": None,
    }

    state = {
        "entity_id": "sensor.kitchen_temperature",
        "state": "21.5",
        "attributes": {
            "friendly_name": "Kitchen Temperature",
            "device_class": "temperature",
            "unit_of_measurement": "°C",
        },
        "last_changed": "2026-07-16T18:00:00+00:00",
        "last_updated": "2026-07-16T18:05:00+00:00",
        "last_reported": "2026-07-16T18:10:00+00:00",
    }

    data = {
        "states": [state],
        "entities": [entity_registry],
        "devices": [
            {
                "id": "device-1",
                "name": "Kitchen Sensor",
                "area_id": "kitchen",
            }
        ],
        "areas": [
            {
                "area_id": "kitchen",
                "name": "Kitchen",
            }
        ],
        "config": {},
        "services": [],
        "labels": [],
    }

    idx = {
        "state_by_entity": {
            "sensor.kitchen_temperature": state,
        },
        "device_by_id": {
            "device-1": data["devices"][0],
        },
        "entities_by_device": {
            "device-1": [entity_registry],
        },
    }

    installation = build_model(data, idx)
    entity = installation.entities["sensor.kitchen_temperature"]

    assert entity.state == "21.5"
    assert entity.attributes["device_class"] == "temperature"
    assert entity.last_changed == "2026-07-16T18:00:00+00:00"
    assert entity.last_updated == "2026-07-16T18:05:00+00:00"
    assert entity.last_reported == "2026-07-16T18:10:00+00:00"
    assert entity.registry["platform"] == "zha"
    assert entity.state_raw["state"] == "21.5"
    assert entity.raw["platform"] == "zha"


def test_builder_handles_missing_state_timestamps():
    entity_registry = {
        "entity_id": "sensor.simple",
        "platform": "test",
        "device_id": None,
        "area_id": None,
    }

    state = {
        "entity_id": "sensor.simple",
        "state": "unknown",
        "attributes": {},
    }

    data = {
        "states": [state],
        "entities": [entity_registry],
        "devices": [],
        "areas": [],
        "config": {},
        "services": [],
        "labels": [],
    }

    idx = {
        "state_by_entity": {
            "sensor.simple": state,
        },
        "device_by_id": {},
        "entities_by_device": {},
    }

    installation = build_model(data, idx)
    entity = installation.entities["sensor.simple"]

    assert entity.last_changed is None
    assert entity.last_updated is None
    assert entity.last_reported is None
    assert entity.attributes == {}
