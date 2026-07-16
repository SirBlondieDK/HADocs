from src.hadocs.core.models import EntityModel
from src.hadocs.intelligence.engine import profile_entity
from src.hadocs.intelligence.profiles import ProfileKind


def make_entity(
    entity_id: str,
    *,
    platform: str = "test",
    importance: str = "normal",
    is_ignored: bool = False,
    attributes: dict | None = None,
    registry: dict | None = None,
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        platform=platform,
        state="unknown",
        area_id=None,
        device_id=None,
        is_ignored=is_ignored,
        is_physical=True,
        importance=importance,
        attributes=attributes or {},
        registry=registry or {},
        raw=registry or {},
    )


def test_button_is_action():
    profile = profile_entity(
        make_entity("button.device_ping")
    )

    assert profile.kind is ProfileKind.ACTION
    assert profile.expected_unknown is True
    assert profile.affects_health is False


def test_event_domain_is_event_driven():
    profile = profile_entity(
        make_entity("event.doorbell")
    )

    assert profile.kind is ProfileKind.EVENT
    assert profile.event_driven is True


def test_diagnostic_category_is_diagnostic():
    profile = profile_entity(
        make_entity(
            "sensor.signal_strength",
            registry={"entity_category": "diagnostic"},
        )
    )

    assert profile.kind is ProfileKind.DIAGNOSTIC
    assert profile.affects_health is False


def test_config_category_is_configuration():
    profile = profile_entity(
        make_entity(
            "number.device_sensitivity",
            registry={"entity_category": "config"},
        )
    )

    assert profile.kind is ProfileKind.CONFIGURATION


def test_connectivity_binary_sensor_is_availability():
    profile = profile_entity(
        make_entity(
            "binary_sensor.device_connected",
            attributes={"device_class": "connectivity"},
        )
    )

    assert profile.kind is ProfileKind.AVAILABILITY
    assert profile.reachability_signal is True


def test_motion_binary_sensor_is_event():
    profile = profile_entity(
        make_entity(
            "binary_sensor.camera_motion",
            attributes={"device_class": "motion"},
        )
    )

    assert profile.kind is ProfileKind.EVENT
    assert profile.affects_health is False


def test_temperature_sensor_is_measurement():
    profile = profile_entity(
        make_entity(
            "sensor.room_temperature",
            attributes={"device_class": "temperature"},
        )
    )

    assert profile.kind is ProfileKind.MEASUREMENT
    assert profile.affects_health is True


def test_switch_is_control():
    profile = profile_entity(
        make_entity("switch.dishwasher")
    )

    assert profile.kind is ProfileKind.CONTROL
    assert profile.reachability_signal is True


def test_update_entity_is_diagnostic():
    profile = profile_entity(
        make_entity("update.device_firmware")
    )

    assert profile.kind is ProfileKind.DIAGNOSTIC


def test_disabled_entity_is_diagnostic():
    profile = profile_entity(
        make_entity(
            "sensor.disabled",
            registry={"disabled_by": "user"},
        )
    )

    assert profile.kind is ProfileKind.DIAGNOSTIC
