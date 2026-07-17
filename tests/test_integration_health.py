from datetime import datetime, timezone

from src.hadocs.core.integration_health import (
    IntegrationHealthStatus,
    calculate_integration_health,
)
from src.hadocs.core.models import (
    DeviceModel,
    EntityModel,
    InstallationModel,
    IntegrationModel,
)


NOW = datetime(2026, 7, 16, 18, 0, 0, tzinfo=timezone.utc)


def make_entity(
    entity_id: str,
    state: str,
    *,
    platform: str = "test",
    importance: str = "normal",
    device_id: str = "device-1",
    last_reported: str | None = None,
    attributes: dict | None = None,
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        platform=platform,
        state=state,
        area_id=None,
        device_id=device_id,
        is_ignored=False,
        is_physical=True,
        importance=importance,
        attributes=attributes or {},
        last_reported=last_reported,
    )


def make_device(
    device_id: str,
    entities: list[EntityModel],
    *,
    name: str | None = None,
) -> DeviceModel:
    return DeviceModel(
        device_id=device_id,
        name=name or device_id,
        area_id=None,
        manufacturer="Test",
        model="Test",
        sw_version="",
        hw_version="",
        classification="physical",
        entities=entities,
    )


def make_model(
    platform: str,
    devices: list[DeviceModel],
) -> InstallationModel:
    entities = [
        entity
        for device in devices
        for entity in device.entities
    ]

    integration = IntegrationModel(
        platform=platform,
        entities=entities,
        devices=devices,
    )

    return InstallationModel(
        areas={},
        devices={
            device.device_id: device
            for device in devices
        },
        entities={
            entity.entity_id: entity
            for entity in entities
        },
        integrations={platform: integration},
        config={},
        states=[],
        services=[],
        labels=[],
        raw={},
    )


def test_unknown_action_entity_count_does_not_reduce_score():
    entities = [
        make_entity(
            f"button.action_{index}",
            "unknown",
            platform="zwave_js",
        )
        for index in range(100)
    ]
    entities.append(
        make_entity(
            "sensor.temperature",
            "21.5",
            platform="zwave_js",
            last_reported="2026-07-16T17:59:00+00:00",
        )
    )

    device = make_device("device-1", entities)
    result = calculate_integration_health(
        make_model("zwave_js", [device]),
        now=NOW,
    )[0]

    assert result.score == 100
    assert result.status is IntegrationHealthStatus.HEALTHY
    assert result.total_entities == 101


def test_sleeping_device_does_not_reduce_score():
    entity = make_entity(
        "sensor.node_status",
        "sleeping",
        platform="zwave_js",
        last_reported="2026-07-16T17:59:00+00:00",
    )

    result = calculate_integration_health(
        make_model(
            "zwave_js",
            [make_device("device-1", [entity])],
        ),
        now=NOW,
    )[0]

    assert result.score == 100
    assert result.sleeping_devices == 1


def test_one_explicit_offline_device_is_warning():
    entity = make_entity(
        "binary_sensor.device_online",
        "off",
        platform="mqtt",
        importance="important",
        last_reported="2026-07-16T17:59:00+00:00",
        attributes={"device_class": "connectivity"},
    )

    result = calculate_integration_health(
        make_model(
            "mqtt",
            [make_device("device-1", [entity], name="Broker Device")],
        ),
        now=NOW,
    )[0]

    assert result.score == 70
    assert result.status is IntegrationHealthStatus.WARNING
    assert result.offline_devices == 1
    assert result.explicit_offline_devices == ("Broker Device",)


def test_two_explicit_offline_devices_make_integration_problem():
    devices = []

    for index in range(2):
        device_id = f"device-{index}"
        entity = make_entity(
            f"binary_sensor.device_{index}_online",
            "off",
            platform="mqtt",
            importance="important",
            device_id=device_id,
            last_reported="2026-07-16T17:59:00+00:00",
            attributes={"device_class": "connectivity"},
        )
        devices.append(
            make_device(
                device_id,
                [entity],
                name=f"Device {index}",
            )
        )

    result = calculate_integration_health(
        make_model("mqtt", devices),
        now=NOW,
    )[0]

    assert result.score == 40
    assert result.status is IntegrationHealthStatus.PROBLEM
    assert result.offline_devices == 2


def test_one_year_old_normal_device_becomes_maintenance():
    entity = make_entity(
        "sensor.old_phone_battery",
        "72",
        platform="mobile_app",
        last_reported="2025-07-16T18:00:00+00:00",
    )

    result = calculate_integration_health(
        make_model(
            "mobile_app",
            [make_device("old-phone", [entity], name="Old Phone")],
        ),
        now=NOW,
    )[0]

    assert result.score == 95
    assert result.status is IntegrationHealthStatus.MAINTENANCE
    assert result.very_stale_devices == 1
    assert result.stale_device_names == ("Old Phone",)


def test_missing_timestamps_do_not_create_stale_penalty():
    entity = make_entity(
        "sensor.temperature",
        "21.5",
        platform="zha",
    )

    result = calculate_integration_health(
        make_model(
            "zha",
            [make_device("device-1", [entity])],
        ),
        now=NOW,
    )[0]

    assert result.score == 100
    assert result.unknown_freshness_devices == 1


def test_integration_score_is_not_based_on_total_entity_count():
    entities = [
        make_entity(
            f"button.action_{index}",
            "unknown",
            platform="mqtt",
        )
        for index in range(500)
    ]

    result = calculate_integration_health(
        make_model(
            "mqtt",
            [make_device("device-1", entities)],
        ),
        now=NOW,
    )[0]

    assert result.total_entities == 500
    assert result.score == 100
