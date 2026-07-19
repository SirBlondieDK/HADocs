from types import SimpleNamespace

from src.hadocs.core.effective_incidents import _hassio_severity


def model_with(states):
    return SimpleNamespace(
        entities={key: SimpleNamespace(state=value) for key, value in states.items()}
    )


def test_many_addon_unknown_sensors_are_not_critical():
    ids = [f"binary_sensor.addon_{i}_korer" for i in range(60)]
    model = model_with({entity_id: "unknown" for entity_id in ids})
    severity, gain = _hassio_severity(model, ids)
    assert severity == "maintenance"
    assert gain == 1


def test_unknown_central_signal_is_maintenance_not_outage():
    entity_id = "binary_sensor.home_assistant_host_korer"
    severity, gain = _hassio_severity(model_with({entity_id: "unknown"}), [entity_id])
    assert severity == "maintenance"
    assert gain == 1


def test_unavailable_supervisor_signal_is_critical():
    entity_id = "binary_sensor.supervisor_status"
    severity, gain = _hassio_severity(model_with({entity_id: "unavailable"}), [entity_id])
    assert severity == "critical"
    assert gain >= 1


def test_unavailable_operating_system_signal_is_warning():
    entity_id = "binary_sensor.home_assistant_operating_system_status"
    severity, gain = _hassio_severity(model_with({entity_id: "unavailable"}), [entity_id])
    assert severity == "warning"
    assert gain <= 2
