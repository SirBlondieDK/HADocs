from __future__ import annotations

import pytest

from hadocs.analyzers.core import analyze as analyze_raw
from hadocs.analyzers.health import calculate_health_score as calculate_raw_health_score
from hadocs.collectors.homeassistant import build_indexes
from hadocs.core.builder import build_model
from hadocs.core.effective_analysis import build_effective_analysis
from hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
    calculate_health_score_v2,
)
from hadocs.core.incidents import build_incidents
from hadocs.core.incidents_v2 import build_incidents_v2
from hadocs.core.relationships import build_relationship_graph


def zha_lqi_entity(
    index: int,
    *,
    disabled_by: object,
    platform: str = "zha",
) -> dict[str, object]:
    return {
        "entity_id": f"sensor.{platform}_node_{index}_lqi",
        "platform": platform,
        "device_id": f"{platform}-device",
        "area_id": None,
        "name": f"{platform.upper()} node {index} link quality",
        "original_name": "Link quality",
        "entity_category": "diagnostic",
        "disabled_by": disabled_by,
    }


def unavailable_state(entity_id: str) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "state": "unavailable",
        "attributes": {
            "friendly_name": entity_id.replace("_", " ").title(),
            "state_class": "measurement",
        },
        "last_changed": "2026-08-01T10:00:00Z",
        "last_updated": "2026-08-01T10:00:00Z",
    }


def zha_data(
    *,
    enabled: int = 0,
    disabled: int = 0,
    disabled_by: object = "integration",
    platform: str = "zha",
    include_disabled_runtime_states: bool = False,
) -> dict[str, object]:
    disabled_entities = [
        zha_lqi_entity(index, disabled_by=disabled_by, platform=platform)
        for index in range(disabled)
    ]
    enabled_entities = [
        zha_lqi_entity(100 + index, disabled_by=None, platform=platform)
        for index in range(enabled)
    ]
    entities = [*disabled_entities, *enabled_entities]
    return {
        "areas": [{"area_id": "mesh", "name": "Mesh"}],
        "devices": [
            {
                "id": f"{platform}-device",
                "name": f"{platform.upper()} mesh device",
                "area_id": "mesh",
                "manufacturer": "Synthetic",
                "model": "Mesh node",
            }
        ],
        "entities": entities,
        "states": [
            unavailable_state(str(entity["entity_id"]))
            for entity in (
                entities if include_disabled_runtime_states else enabled_entities
            )
        ],
        "config": {},
        "services": [],
        "labels": [],
    }


def product_analysis(data: dict[str, object]):
    indexes = build_indexes(data)
    model = build_model(data, indexes)
    graph = build_relationship_graph(model)
    device_health = calculate_device_health(model)
    score, notes = calculate_health_score(model, device_health)
    analysis = build_effective_analysis(
        model,
        build_incidents(model, graph),
        (),
        score,
    )
    score_v2 = calculate_health_score_v2(model, list(analysis.root_causes))
    return model, device_health, score, notes, analysis, score_v2


def entity_ids(items: list[dict[str, object]]) -> set[str]:
    return {str(item["entity_id"]) for item in items}


@pytest.mark.parametrize("disabled_by", ["user", "integration", "config_entry"])
def test_disabled_zha_lqi_is_inventory_but_not_an_analysis_signal(disabled_by: str):
    data = zha_data(disabled=6, disabled_by=disabled_by)
    model, device_health, score, notes, analysis, score_v2 = product_analysis(data)
    raw = analyze_raw(data, build_indexes(data))
    raw_score, raw_notes = calculate_raw_health_score(raw)
    expected_ids = {f"sensor.zha_node_{index}_lqi" for index in range(6)}

    assert set(model.entities) == expected_ids
    assert all(entity.registry["disabled_by"] == disabled_by for entity in model.entities.values())
    assert all(entity.raw["disabled_by"] == disabled_by for entity in model.entities.values())
    assert all(entity.is_ignored for entity in model.entities.values())

    assert device_health == []
    assert score == 100
    assert notes == []
    assert analysis.raw_incidents == ()
    assert analysis.effective_incidents == ()
    assert analysis.root_causes == ()
    assert analysis.recommendations == ()
    assert analysis.potential_gain == 0
    assert analysis.executive.score == 100
    assert analysis.executive.potential_score == 100
    assert build_incidents_v2(model) == []
    assert score_v2.score == 100
    assert score_v2.potential_score == 100
    assert score_v2.affected_active_entities == 0
    assert score_v2.disabled_entities_ignored == 6

    assert entity_ids(raw["ignored_entities"]) == expected_ids
    assert raw["physical_entities"] == []
    assert raw["real_unavailable"] == []
    assert raw["real_unknown"] == []
    assert raw["ignored_unknown_unavailable"] == []
    assert not any(raw["dashboard_candidates_by_area"].values())
    assert raw_score == 100
    assert raw_notes == []


def test_stale_runtime_state_for_disabled_zha_lqi_is_also_ignored():
    data = zha_data(disabled=6, include_disabled_runtime_states=True)
    raw = analyze_raw(data, build_indexes(data))
    raw_score, raw_notes = calculate_raw_health_score(raw)

    assert raw["real_unavailable"] == []
    assert len(raw["ignored_unknown_unavailable"]) == 6
    assert raw_score == 100
    assert raw_notes == ["6 system/service entities were ignored in Health Score"]


def test_enabled_zha_lqi_preserves_existing_analytical_behavior():
    data = zha_data(enabled=6)
    model, device_health, score, _notes, analysis, score_v2 = product_analysis(data)
    raw = analyze_raw(data, build_indexes(data))
    expected_ids = {f"sensor.zha_node_{100 + index}_lqi" for index in range(6)}
    incident = analysis.root_causes[0]

    assert all(not entity.is_ignored for entity in model.entities.values())
    assert len(device_health) == 1
    assert device_health[0].status == "healthy"
    assert device_health[0].score == 100
    assert score == 100
    assert len(analysis.root_causes) == 1
    assert set(incident.affected_entities) == expected_ids
    assert incident.affected_integrations == ["zha"]
    assert incident.severity == "maintenance"
    assert incident.estimated_score_gain == 2
    assert len(analysis.recommendations) == 1
    assert score_v2.score == 90
    assert score_v2.potential_score == 98
    assert score_v2.affected_active_entities == 6

    assert raw["ignored_entities"] == []
    assert entity_ids(raw["physical_entities"]) == expected_ids
    assert entity_ids(raw["real_unavailable"]) == expected_ids
    assert raw["ignored_unknown_unavailable"] == []


def test_disabled_zha_lqi_does_not_inflate_mixed_severity_gain_or_score():
    enabled_only = product_analysis(zha_data(enabled=6))
    mixed = product_analysis(zha_data(enabled=6, disabled=6))
    (
        _enabled_model,
        enabled_health,
        enabled_score,
        enabled_notes,
        enabled_analysis,
        enabled_v2,
    ) = enabled_only
    (
        mixed_model,
        mixed_health,
        mixed_score,
        mixed_notes,
        mixed_analysis,
        mixed_v2,
    ) = mixed

    enabled_incident = enabled_analysis.root_causes[0]
    mixed_incident = mixed_analysis.root_causes[0]
    enabled_ids = {f"sensor.zha_node_{100 + index}_lqi" for index in range(6)}
    disabled_ids = {f"sensor.zha_node_{index}_lqi" for index in range(6)}

    assert len(mixed_model.entities) == 12
    assert set(mixed_incident.affected_entities) == enabled_ids
    assert disabled_ids.isdisjoint(mixed_incident.affected_entities)
    assert mixed_incident.severity == enabled_incident.severity == "maintenance"
    assert mixed_incident.estimated_score_gain == enabled_incident.estimated_score_gain == 2
    assert mixed_score == enabled_score
    assert mixed_notes == enabled_notes
    assert [(item.status, item.score, item.reasons) for item in mixed_health] == [
        (item.status, item.score, item.reasons) for item in enabled_health
    ]
    assert mixed_analysis.executive.score == enabled_analysis.executive.score
    assert mixed_analysis.executive.potential_score == enabled_analysis.executive.potential_score
    assert mixed_analysis.potential_gain == enabled_analysis.potential_gain
    assert len(mixed_analysis.recommendations) == len(enabled_analysis.recommendations)
    assert mixed_v2.score == enabled_v2.score == 90
    assert mixed_v2.potential_score == enabled_v2.potential_score == 98
    assert mixed_v2.affected_active_entities == enabled_v2.affected_active_entities == 6


def test_registry_disabled_policy_is_platform_neutral_for_zha_and_zwave_js():
    for platform in ("zha", "zwave_js"):
        data = zha_data(disabled=6, platform=platform)
        model, _health, score, _notes, analysis, score_v2 = product_analysis(data)
        raw = analyze_raw(data, build_indexes(data))

        assert len(model.entities) == 6
        assert score == 100
        assert analysis.root_causes == ()
        assert score_v2.affected_active_entities == 0
        assert raw["real_unavailable"] == []
        assert raw["ignored_unknown_unavailable"] == []


def test_hidden_unknown_or_unavailable_is_not_confused_with_registry_disabled():
    data = zha_data(enabled=6)
    for entity in data["entities"]:
        entity["hidden_by"] = "user"
    data["states"][0]["state"] = "unknown"

    model, _health, _score, _notes, analysis, _score_v2 = product_analysis(data)
    raw = analyze_raw(data, build_indexes(data))

    assert all(not entity.is_ignored for entity in model.entities.values())
    assert len(analysis.root_causes) == 1
    assert len(raw["real_unavailable"]) == 5
    assert len(raw["real_unknown"]) == 1


def test_missing_empty_or_malformed_registry_metadata_is_safe_and_enabled():
    data = zha_data(enabled=6)
    data["entities"][0].pop("disabled_by")
    data["entities"][0]["entity_registry"] = []
    data["entities"][1]["disabled_by"] = ""
    data["entities"][1]["registry"] = "malformed"
    data["entities"][2]["raw"] = 42

    model, _health, score, _notes, analysis, _score_v2 = product_analysis(data)
    raw = analyze_raw(data, build_indexes(data))

    assert all(not entity.is_ignored for entity in model.entities.values())
    assert score == 100
    assert len(analysis.root_causes) == 1
    assert len(analysis.root_causes[0].affected_entities) == 6
    assert len(raw["real_unavailable"]) == 6


def test_malformed_non_null_disabled_marker_fails_closed_without_exception():
    data = zha_data(disabled=1, disabled_by={"unexpected": "shape"})

    model, device_health, score, _notes, analysis, _score_v2 = product_analysis(data)
    raw = analyze_raw(data, build_indexes(data))

    assert all(entity.is_ignored for entity in model.entities.values())
    assert device_health == []
    assert score == 100
    assert analysis.root_causes == ()
    assert len(raw["ignored_entities"]) == 1
    assert raw["physical_entities"] == []


def test_existing_domain_and_name_ignore_rules_are_unchanged():
    data = zha_data(enabled=2)
    data["entities"][0]["entity_id"] = "button.zha_node_ping"
    data["entities"][1]["entity_id"] = "sensor.zha_node_linkquality"
    data["states"][0] = unavailable_state("button.zha_node_ping")
    data["states"][1] = unavailable_state("sensor.zha_node_linkquality")

    raw = analyze_raw(data, build_indexes(data))

    assert entity_ids(raw["ignored_entities"]) == {
        "button.zha_node_ping",
        "sensor.zha_node_linkquality",
    }
    assert raw["real_unavailable"] == []


def test_zha_disabled_filtering_is_deterministic_across_input_order():
    data = zha_data(enabled=6, disabled=6)
    reversed_data = {
        **data,
        "entities": list(reversed(data["entities"])),
        "states": list(reversed(data["states"])),
    }

    first = product_analysis(data)[4]
    second = product_analysis(reversed_data)[4]

    assert [incident.incident_id for incident in first.root_causes] == [
        incident.incident_id for incident in second.root_causes
    ]
    assert [incident.affected_entities for incident in first.root_causes] == [
        incident.affected_entities for incident in second.root_causes
    ]
    assert first.executive == second.executive
