from __future__ import annotations

from hadocs.advisor.engine import build_action_plan_from_incidents
from hadocs.collectors.homeassistant import build_indexes
from hadocs.core.builder import build_model
from hadocs.core.effective_analysis import build_effective_analysis
from hadocs.core.effective_incidents import filter_effective_incidents
from hadocs.core.entity_eligibility import (
    is_disabled_entity,
    registry_disabled_by,
)
from hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
    calculate_health_score_v2,
)
from hadocs.core.history import _problem_entities
from hadocs.core.incidents import Incident, build_incidents
from hadocs.core.incidents_v2 import build_incidents_v2
from hadocs.core.models import DeviceModel, EntityModel, InstallationModel, IntegrationModel
from hadocs.core.relationships import build_relationship_graph
from hadocs.core.state_interpreter import StateMeaning, interpret_entity_state
from hadocs.intelligence.engine import profile_entity
from hadocs.intelligence.profiles import ProfileKind
from hadocs.reports.generator import generate_maintenance, generate_root_causes


def registry_entity(
    entity_id: str,
    *,
    platform: str,
    disabled_by: object = None,
    device_id: str | None = None,
) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "platform": platform,
        "device_id": device_id,
        "area_id": None,
        "name": entity_id,
        "disabled_by": disabled_by,
    }


def runtime_state(entity_id: str, state: str) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "state": state,
        "attributes": {},
        "last_changed": "2026-07-30T10:00:00Z",
        "last_updated": "2026-07-30T10:00:00Z",
    }


def build_synthetic_model(
    entities: list[dict[str, object]],
    states: list[dict[str, object]] | None = None,
    devices: list[dict[str, object]] | None = None,
) -> InstallationModel:
    data = {
        "areas": [],
        "devices": devices or [],
        "entities": entities,
        "states": states or [],
        "config": {},
        "services": [],
        "labels": [],
    }
    return build_model(data, build_indexes(data))


def analyze(model: InstallationModel):
    graph = build_relationship_graph(model)
    device_health = calculate_device_health(model)
    score, _ = calculate_health_score(model, device_health)
    raw = build_incidents(model, graph)
    return build_effective_analysis(model, raw, (), score)


def test_registry_only_disabled_metadata_survives_and_is_ignored():
    for marker in ("user", "integration", "future_owner"):
        entity_id = f"sensor.registry_only_{marker}"
        model = build_synthetic_model(
            [registry_entity(entity_id, platform="systemmonitor", disabled_by=marker)]
        )
        entity = model.entities[entity_id]

        assert entity.state == "unknown"
        assert entity.registry["disabled_by"] == marker
        assert entity.raw["disabled_by"] == marker
        assert registry_disabled_by(entity) == marker
        assert is_disabled_entity(entity)
        assert entity.is_ignored
        assert profile_entity(entity).kind is ProfileKind.DIAGNOSTIC
        assert interpret_entity_state(entity).meaning is StateMeaning.IGNORED


def test_disabled_without_state_creates_no_fault_surface_or_score_effect():
    baseline = build_synthetic_model([])
    baseline_analysis = analyze(baseline)
    baseline_v2 = calculate_health_score_v2(baseline, [])

    for marker in ("user", "integration"):
        entities = [
            registry_entity(
                f"sensor.disabled_{index}",
                platform="synthetic",
                disabled_by=marker,
            )
            for index in range(12)
        ]
        model = build_synthetic_model(entities)
        analysis = analyze(model)
        v2 = calculate_health_score_v2(model, list(analysis.root_causes))
        disabled_only_incident = Incident(
            incident_id="integration:disabled-only",
            title="Disabled only",
            category="integration",
            severity="critical",
            root_cause="disabled-only",
            affected_entities=["sensor.disabled_0"],
            estimated_score_gain=10,
        )
        raw_v2 = calculate_health_score_v2(model, [disabled_only_incident])

        assert analysis.raw_incidents == ()
        assert analysis.effective_incidents == ()
        assert analysis.root_causes == ()
        assert analysis.recommendations == ()
        assert analysis.potential_gain == 0
        assert analysis.executive.score == baseline_analysis.executive.score
        assert analysis.executive.potential_score == baseline_analysis.executive.potential_score
        assert v2.score == baseline_v2.score
        assert v2.potential_score == baseline_v2.potential_score
        assert v2.affected_active_entities == 0
        assert raw_v2.score == baseline_v2.score
        assert raw_v2.potential_score == baseline_v2.potential_score
        assert raw_v2.affected_active_entities == 0


def test_common_effective_filter_rejects_registry_disabled_incident():
    entity_id = "sensor.disabled_candidate"
    model = build_synthetic_model(
        [registry_entity(entity_id, platform="synthetic", disabled_by="user")]
    )
    incident = Incident(
        incident_id="integration:synthetic",
        title="Synthetic issue",
        category="integration",
        severity="warning",
        root_cause="synthetic",
        affected_entities=[entity_id],
        affected_integrations=["synthetic"],
        recommendation="Incorrect recommendation",
        estimated_score_gain=10,
    )

    assert filter_effective_incidents(model, [incident]) == []


def test_disabled_runtime_reachability_signal_cannot_create_v2_incident():
    disabled = EntityModel(
        entity_id="binary_sensor.node_online",
        name="Node online",
        domain="binary_sensor",
        platform="mqtt",
        state="off",
        area_id=None,
        device_id="device-1",
        is_ignored=False,
        is_physical=True,
        importance="important",
        registry={"disabled_by": "integration"},
        raw={"disabled_by": "integration"},
    )
    healthy = EntityModel(
        entity_id="sensor.node_temperature",
        name="Node temperature",
        domain="sensor",
        platform="mqtt",
        state="21.0",
        area_id=None,
        device_id="device-1",
        is_ignored=False,
        is_physical=True,
    )
    model = model_with_device([disabled, healthy], platform="mqtt")

    assert build_incidents_v2(model) == []
    health = calculate_device_health(model)
    assert len(health) == 1
    assert health[0].score == 100
    assert not any("confirmed unavailable-state faults" in reason for reason in health[0].reasons)


def test_enabled_unavailable_entity_remains_a_legitimate_fault():
    unavailable = EntityModel(
        entity_id="switch.enabled_fault",
        name="Enabled fault",
        domain="switch",
        platform="mqtt",
        state="unavailable",
        area_id=None,
        device_id="device-1",
        is_ignored=False,
        is_physical=True,
        importance="important",
        registry={"disabled_by": None},
    )
    model = model_with_device([unavailable], platform="mqtt")

    health = calculate_device_health(model)
    incidents = build_incidents_v2(model)

    assert health[0].status == "warning"
    assert any("confirmed unavailable-state faults" in reason for reason in health[0].reasons)
    assert any(
        incident.affected_entities == ["switch.enabled_fault"]
        for incident in incidents
    )


def test_mixed_integration_uses_only_enabled_fault_population():
    disabled = [
        registry_entity(
            f"sensor.mixed_disabled_{index}",
            platform="mixed",
            disabled_by="user" if index % 2 else "integration",
        )
        for index in range(60)
    ]
    enabled = [
        registry_entity(f"sensor.mixed_fault_{index}", platform="mixed")
        for index in range(6)
    ]
    states = [
        runtime_state(f"sensor.mixed_fault_{index}", "unavailable")
        for index in range(6)
    ]
    model = build_synthetic_model([*disabled, *enabled], states)
    analysis = analyze(model)
    incident = next(
        item for item in analysis.root_causes if item.affected_integrations == ["mixed"]
    )
    eligible_ids = {f"sensor.mixed_fault_{index}" for index in range(6)}

    assert set(incident.affected_entities) == eligible_ids
    assert len(incident.affected_entities) == 6
    assert incident.estimated_score_gain == 2
    enabled_only = build_synthetic_model(enabled, states)
    enabled_only_incident = next(
        item
        for item in analyze(enabled_only).root_causes
        if item.affected_integrations == ["mixed"]
    )
    assert incident.estimated_score_gain == enabled_only_incident.estimated_score_gain
    assert analysis.top_recommendation_gain == 0
    assert set(analysis.executive.actions[0].related_items).issubset(eligible_ids)
    assert not any("disabled" in item for item in incident.affected_entities)


def test_large_systemmonitor_and_zwave_populations_do_not_inflate_results():
    systemmonitor_disabled = [
        registry_entity(
            f"sensor.systemmonitor_disabled_{index}",
            platform="systemmonitor",
            disabled_by="user" if index < 110 else "integration",
        )
        for index in range(217)
    ]
    systemmonitor_enabled = [
        registry_entity(f"sensor.systemmonitor_live_{index}", platform="systemmonitor")
        for index in range(6)
    ]
    systemmonitor_states = [
        runtime_state(f"sensor.systemmonitor_live_{index}", str(index))
        for index in range(6)
    ]
    systemmonitor = build_synthetic_model(
        [*systemmonitor_disabled, *systemmonitor_enabled],
        systemmonitor_states,
    )

    assert analyze(systemmonitor).root_causes == ()

    zwave_disabled = [
        registry_entity(
            f"sensor.zwave_disabled_{index}",
            platform="zwave_js",
            disabled_by="integration",
        )
        for index in range(120)
    ]
    diagnostic_stubs = [
        registry_entity(f"button.node_ping_{index}", platform="zwave_js")
        for index in range(20)
    ]
    enabled_faults = [
        registry_entity(f"sensor.zwave_fault_{index}", platform="zwave_js")
        for index in range(6)
    ]
    states = [
        runtime_state(f"sensor.zwave_fault_{index}", "unavailable")
        for index in range(6)
    ]
    zwave = build_synthetic_model(
        [*zwave_disabled, *diagnostic_stubs, *enabled_faults], states
    )
    analysis = analyze(zwave)
    incident = next(
        item for item in analysis.root_causes if item.affected_integrations == ["zwave_js"]
    )

    assert len(incident.affected_entities) == 6
    assert all("zwave_fault" in entity_id for entity_id in incident.affected_entities)
    assert incident.estimated_score_gain == 2


def test_reports_history_and_relationships_use_the_effective_population(tmp_path):
    disabled = [
        registry_entity(
            f"sensor.report_disabled_{index}",
            platform="report_test",
            disabled_by="user",
        )
        for index in range(8)
    ]
    model = build_synthetic_model(disabled)
    graph = build_relationship_graph(model)
    analysis = analyze(model)

    generate_root_causes(tmp_path, list(analysis.root_causes), "synthetic-time")
    generate_maintenance(
        tmp_path,
        analysis.executive,
        list(analysis.root_causes),
        "synthetic-time",
    )
    rendered = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(tmp_path.glob("*.md"))
    )

    assert _problem_entities(model) == []
    assert graph.integrations["report_test"].problem_entities == []
    assert build_action_plan_from_incidents(list(analysis.root_causes)) == []
    assert "report_disabled" not in rendered
    assert "Estimated score gain: `+" not in rendered


def model_with_device(
    entities: list[EntityModel], *, platform: str
) -> InstallationModel:
    device = DeviceModel(
        device_id="device-1",
        name="Synthetic Device",
        area_id=None,
        manufacturer="Synthetic",
        model="Device",
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
        entities={entity.entity_id: entity for entity in entities},
        integrations={platform: integration},
        config={},
        states=[],
        services=[],
        labels=[],
        raw={},
    )
