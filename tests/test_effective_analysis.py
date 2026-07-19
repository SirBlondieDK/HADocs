from types import SimpleNamespace

from src.hadocs.core.effective_analysis import build_effective_analysis
from src.hadocs.core.incidents import Incident


def _model(entity_state="unavailable"):
    entity = SimpleNamespace(
        entity_id="sensor.pool_status",
        device_id="pool-id",
        state=entity_state,
        disabled_by=None,
        disabled=False,
        registry={},
        raw={},
    )
    device = SimpleNamespace(device_id="pool-id", name="Pool", entities=[entity])
    return SimpleNamespace(
        entities={entity.entity_id: entity},
        devices={device.device_id: device},
    )


def _incident():
    return Incident(
        incident_id="pool",
        title="Device issue: Pool",
        category="physical_device",
        severity="warning",
        root_cause="Pool",
        affected_entities=["sensor.pool_status"],
        affected_devices=["Pool"],
        recommendation="Turn it on",
        estimated_score_gain=5,
        estimated_repair_minutes=20,
    )


def test_analysis_suppresses_expected_offline_and_all_consumers_see_no_issue(monkeypatch):
    import src.hadocs.core.effective_analysis as module

    monkeypatch.setattr(
        module,
        "filter_effective_incidents",
        lambda model, incidents, overrides: [],
    )
    result = build_effective_analysis(_model(), [_incident()], (), 99)

    assert result.effective_incidents == ()
    assert result.root_causes == ()
    assert result.recommendations == ()
    assert result.executive.main_cause == "No major issue detected"
    assert result.executive.potential_score == 99
    assert result.suppressed_incident_count == 1


def test_top_recommendation_gain_cannot_exceed_score_headroom(monkeypatch):
    import src.hadocs.core.effective_analysis as module

    monkeypatch.setattr(
        module,
        "filter_effective_incidents",
        lambda model, incidents, overrides: list(incidents),
    )
    result = build_effective_analysis(_model(), [_incident()], (), 99)

    assert result.executive.potential_score == 100
    assert result.top_recommendation_gain == 1
