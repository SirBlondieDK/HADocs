from src.hadocs.core.models import EntityModel
from src.hadocs.core.state_interpreter import (
    StateMeaning,
    interpret_entity_state,
)


def make_entity(
    entity_id: str,
    state: str,
    *,
    domain: str | None = None,
    importance: str = "normal",
    is_ignored: bool = False,
    raw: dict | None = None,
) -> EntityModel:
    resolved_domain = domain or entity_id.split(".", maxsplit=1)[0]

    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=resolved_domain,
        platform="test",
        state=state,
        area_id=None,
        device_id=None,
        is_ignored=is_ignored,
        is_physical=True,
        importance=importance,
        raw=raw or {},
    )


def test_stateless_button_unknown_is_expected():
    result = interpret_entity_state(
        make_entity("button.office_ping", "unknown")
    )

    assert result.meaning is StateMeaning.EXPECTED_UNKNOWN
    assert result.fault_weight == 0


def test_battery_replaced_button_unknown_is_expected():
    result = interpret_entity_state(
        make_entity(
            "button.motion_sensor_battery_replaced",
            "unknown",
        )
    )

    assert result.meaning is StateMeaning.EXPECTED_UNKNOWN
    assert result.fault_weight == 0


def test_holding_until_unknown_is_expected():
    result = interpret_entity_state(
        make_entity(
            "sensor.thermostat_holding_until",
            "unknown",
        )
    )

    assert result.meaning is StateMeaning.EXPECTED_UNKNOWN


def test_unknown_measurement_is_only_weak_signal():
    result = interpret_entity_state(
        make_entity("sensor.temperature", "unknown")
    )

    assert result.meaning is StateMeaning.TRANSIENT
    assert result.fault_weight == 1


def test_unavailable_important_entity_is_fault():
    result = interpret_entity_state(
        make_entity(
            "switch.dishwasher",
            "unavailable",
            importance="important",
        )
    )

    assert result.meaning is StateMeaning.FAULT
    assert result.fault_weight == 8


def test_disabled_entity_is_ignored():
    result = interpret_entity_state(
        make_entity(
            "sensor.disabled",
            "unavailable",
            raw={"disabled_by": "user"},
        )
    )

    assert result.meaning is StateMeaning.IGNORED
    assert result.fault_weight == 0


def test_normal_state_is_healthy():
    result = interpret_entity_state(
        make_entity("binary_sensor.motion", "off")
    )

    assert result.meaning is StateMeaning.HEALTHY
    assert result.fault_weight == 0
