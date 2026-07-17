from src.hadocs.core.device_reachability import (
    ReachabilityStatus,
    determine_device_reachability,
)
from src.hadocs.core.models import DeviceModel, EntityModel


def make_entity(
    entity_id: str,
    state: str,
    *,
    importance: str = "normal",
    is_ignored: bool = False,
    is_physical: bool = True,
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        platform="test",
        state=state,
        area_id=None,
        device_id="device-1",
        is_ignored=is_ignored,
        is_physical=is_physical,
        importance=importance,
    )


def make_device(
    entities: list[EntityModel],
) -> DeviceModel:
    return DeviceModel(
        device_id="device-1",
        name="Test Device",
        area_id=None,
        manufacturer="Test",
        model="Test",
        sw_version="",
        hw_version="",
        classification="physical",
        entities=entities,
    )


def test_explicit_online_entity_marks_device_online():
    device = make_device(
        [
            make_entity(
                "binary_sensor.device_online",
                "on",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.ONLINE
    assert result.confidence == 95


def test_explicit_offline_entity_marks_device_offline():
    device = make_device(
        [
            make_entity(
                "binary_sensor.device_online",
                "off",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.OFFLINE
    assert result.confidence == 95


def test_dead_node_status_marks_device_offline():
    device = make_device(
        [
            make_entity(
                "sensor.device_node_status",
                "dead",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.OFFLINE


def test_sleeping_node_is_not_offline():
    device = make_device(
        [
            make_entity(
                "sensor.device_node_status",
                "sleeping",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.SLEEPING
    assert result.is_offline is False


def test_healthy_primary_entity_supports_online_status():
    device = make_device(
        [
            make_entity(
                "sensor.room_temperature",
                "21.5",
            ),
            make_entity(
                "button.device_ping",
                "unknown",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.ONLINE
    assert result.confidence == 70


def test_only_expected_unknown_entities_do_not_mark_device_offline():
    device = make_device(
        [
            make_entity("button.device_ping", "unknown"),
            make_entity(
                "button.device_battery_replaced",
                "unknown",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.UNKNOWN
    assert result.is_offline is False


def test_all_important_entities_unavailable_supports_offline_status():
    device = make_device(
        [
            make_entity(
                "switch.dishwasher",
                "unavailable",
                importance="important",
            ),
        ]
    )

    result = determine_device_reachability(device)

    assert result.status is ReachabilityStatus.OFFLINE
    assert result.confidence == 65
