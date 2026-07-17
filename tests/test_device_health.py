from src.hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
)
from src.hadocs.core.models import DeviceModel, EntityModel, InstallationModel


class Model:
    devices = {}
    entities = {}


def make_entity(
    entity_id: str,
    state: str,
    *,
    importance: str = "normal",
    is_ignored: bool = False,
    is_physical: bool = True,
    raw: dict | None = None,
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        platform="test",
        state=state,
        area_id="test-area",
        device_id="device-1",
        is_ignored=is_ignored,
        is_physical=is_physical,
        importance=importance,
        raw=raw or {},
    )


def make_installation(
    entities: list[EntityModel],
) -> InstallationModel:
    device = DeviceModel(
        device_id="device-1",
        name="Test Device",
        area_id="test-area",
        manufacturer="Test",
        model="Test",
        sw_version="",
        hw_version="",
        classification="physical",
        entities=entities,
    )

    return InstallationModel(
        areas={},
        devices={device.device_id: device},
        entities={
            entity.entity_id: entity
            for entity in entities
        },
        integrations={},
        config={},
        states=[],
        services=[],
        labels=[],
        raw={},
    )


def test_empty_model_health_is_perfect():
    score, notes = calculate_health_score(Model(), [])

    assert score == 100


def test_expected_unknown_zwave_actions_do_not_reduce_health():
    installation = make_installation(
        [
            make_entity("button.office_ping", "unknown"),
            make_entity(
                "button.office_battery_replaced",
                "unknown",
            ),
            make_entity("binary_sensor.office_motion", "off"),
        ]
    )

    health = calculate_device_health(installation)

    assert len(health) == 1
    assert health[0].score == 100
    assert health[0].status == "healthy"
    assert health[0].reasons == []


def test_camera_event_sensor_unknown_does_not_reduce_health():
    installation = make_installation(
        [
            make_entity(
                "binary_sensor.camera_line_crossing",
                "unknown",
                raw={"device_class": "motion"},
            ),
            make_entity("camera.front_door", "streaming"),
        ]
    )

    health = calculate_device_health(installation)

    assert health[0].score == 100
    assert health[0].status == "healthy"


def test_unknown_measurement_only_causes_small_penalty():
    installation = make_installation(
        [
            make_entity("sensor.room_temperature", "unknown"),
        ]
    )

    health = calculate_device_health(installation)

    assert health[0].score == 99
    assert health[0].status == "healthy"
    assert "weak unknown-state signals" in health[0].reasons[0]


def test_offline_important_device_is_prioritized():
    installation = make_installation(
        [
            make_entity(
                "switch.dishwasher",
                "unavailable",
                importance="important",
            ),
        ]
    )

    health = calculate_device_health(installation)

    assert health[0].score == 92
    assert health[0].status == "warning"
    assert "confirmed unavailable-state faults" in health[0].reasons[0]


def test_disabled_unavailable_entity_is_ignored():
    installation = make_installation(
        [
            make_entity(
                "sensor.disabled_temperature",
                "unavailable",
                raw={"disabled_by": "user"},
            ),
            make_entity("sensor.healthy_temperature", "21.5"),
        ]
    )

    health = calculate_device_health(installation)

    assert health[0].score == 100
    assert health[0].status == "healthy"


def test_many_expected_unknown_entities_do_not_overwhelm_healthy_device():
    entities = [
        make_entity(f"button.device_ping_{index}", "unknown")
        for index in range(10)
    ]

    entities.extend(
        make_entity(
            f"button.device_battery_replaced_{index}",
            "unknown",
        )
        for index in range(10)
    )

    entities.append(
        make_entity("binary_sensor.device_online", "on")
    )

    installation = make_installation(entities)

    health = calculate_device_health(installation)

    assert health[0].score == 100
    assert health[0].status == "healthy"
