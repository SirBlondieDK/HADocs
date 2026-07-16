from src.hadocs.core.classifiers import classify_device


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
        domains={"sensor"},
        platforms={"test"},
    )

    assert isinstance(result, str)
