from src.hadocs.core.models import (
    AreaModel,
    DeviceModel,
    EntityModel,
    InstallationModel,
    IntegrationModel,
)


def build_installation() -> InstallationModel:
    area = AreaModel(area_id="kitchen", name="Kitchen")

    device = DeviceModel(
        device_id="device-1",
        name="Kitchen Sensor",
        area_id="kitchen",
        manufacturer="Test",
        model="Sensor",
        sw_version="",
        hw_version="",
        classification="physical",
    )

    entity = EntityModel(
        entity_id="sensor.kitchen_temperature",
        name="Kitchen Temperature",
        domain="sensor",
        platform="zha",
        state="unavailable",
        area_id="kitchen",
        device_id="device-1",
        is_ignored=False,
        is_physical=True,
    )

    device.entities.append(entity)
    area.devices.append(device)
    area.entities.append(entity)

    integration = IntegrationModel(
        platform="zha",
        entities=[entity],
        devices=[device],
    )

    return InstallationModel(
        areas={"kitchen": area},
        devices={"device-1": device},
        entities={entity.entity_id: entity},
        integrations={"zha": integration},
        config={},
        states=[],
        services=[],
        labels=[],
        raw={},
    )


def test_installation_relationship_helpers():
    installation = build_installation()

    assert installation.area_for_entity(
        "sensor.kitchen_temperature"
    ).area_id == "kitchen"

    assert installation.device_for_entity(
        "sensor.kitchen_temperature"
    ).device_id == "device-1"


def test_installation_filter_helpers():
    installation = build_installation()

    assert installation.entities_for_platform("zha")
    assert installation.unavailable_entities()
    assert installation.unknown_entities() == []
    assert installation.physical_devices()
