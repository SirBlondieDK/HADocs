from src.hadocs.core.classifiers import classify_device, classify_entity


def test_classify_device_accepts_non_string_registry_values():
    device = {
        "id": "test-device",
        "manufacturer": 123,
        "model": 456,
        "name": 789,
        "name_by_user": None,
    }

    result = classify_device(
        device,
        entity_domains={"sensor"},
        entity_platforms={"test"},
    )

    assert result in {"physical", "virtual", "system"}


def test_classify_entity_accepts_non_string_platform():
    result = classify_entity(
        "sensor.test",
        123,
    )

    assert isinstance(result, tuple)
    assert len(result) == 4
