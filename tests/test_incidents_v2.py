from src.hadocs.core.incidents_v2 import build_incidents_v2
from src.hadocs.core.models import (
    DeviceModel,
    EntityModel,
    InstallationModel,
    IntegrationModel,
)


def make_entity(
    entity_id: str,
    state: str,
    *,
    platform: str = "test",
    importance: str = "normal",
    raw: dict | None = None,
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        platform=platform,
        state=state,
        area_id=None,
        device_id="device-1",
        is_ignored=False,
        is_physical=True,
        importance=importance,
        raw=raw or {},
    )


def make_installation(
    entities: list[EntityModel],
    *,
    platform: str = "test",
) -> InstallationModel:
    device = DeviceModel(
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

    integration = IntegrationModel(
        platform=platform,
        entities=entities,
        devices=[device],
    )

    return InstallationModel(
        areas={},
        devices={device.device_id: device},
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


def test_expected_unknown_entities_create_no_incidents():
    entities = [
        make_entity(
            f"button.node_ping_{index}",
            "unknown",
            platform="zwave_js",
        )
        for index in range(40)
    ]

    model = make_installation(
        entities,
        platform="zwave_js",
    )

    assert build_incidents_v2(model) == []


def test_sleeping_device_creates_no_incident():
    entity = make_entity(
        "sensor.node_status",
        "sleeping",
        platform="zwave_js",
    )

    model = make_installation(
        [entity],
        platform="zwave_js",
    )

    assert build_incidents_v2(model) == []


def test_offline_important_device_creates_warning():
    entity = make_entity(
        "switch.dishwasher",
        "unavailable",
        platform="smartthings",
        importance="important",
    )

    model = make_installation(
        [entity],
        platform="smartthings",
    )

    incidents = build_incidents_v2(model)
    device_incident = next(
        incident
        for incident in incidents
        if incident.category == "physical_device"
    )

    assert device_incident.severity == "warning"
    assert device_incident.root_cause == "Test Device"
    assert device_incident.affected_entities == [
        "switch.dishwasher"
    ]


def test_explicit_offline_signal_creates_critical_device_incident():
    entity = make_entity(
        "binary_sensor.device_online",
        "off",
        platform="mqtt",
        importance="important",
    )

    model = make_installation(
        [entity],
        platform="mqtt",
    )

    incidents = build_incidents_v2(model)
    device_incident = next(
        incident
        for incident in incidents
        if incident.category == "physical_device"
    )

    assert device_incident.severity == "critical"
    assert device_incident.confidence == 95


def test_integration_severity_is_not_based_on_entity_count():
    entities = [
        make_entity(
            f"button.action_{index}",
            "unknown",
            platform="mqtt",
        )
        for index in range(100)
    ]

    entities.append(
        make_entity(
            "switch.real_device",
            "unavailable",
            platform="mqtt",
            importance="important",
        )
    )

    model = make_installation(
        entities,
        platform="mqtt",
    )

    incidents = build_incidents_v2(model)
    integration_incident = next(
        incident
        for incident in incidents
        if incident.category == "integration"
    )

    assert integration_incident.severity == "warning"
    assert integration_incident.affected_entities == [
        "switch.real_device"
    ]
    assert integration_incident.affected_devices == [
        "Test Device"
    ]
