from __future__ import annotations

import json

import pytest

from hadocs.core.models import EntityModel, InstallationModel
from hadocs.core.relationships import (
    NormalizedRelationshipCandidate,
    RelationshipDirection,
    RelationshipEvidenceOrigin,
    RelationshipIneligibilityReason,
    RelationshipPredicate,
    RelationshipTargetKind,
    build_relationship_candidates,
    build_relationship_graph,
    make_relationship_candidate,
    serialize_relationship_candidates,
)


def _entity(
    entity_id: str = "light.private_kitchen",
    *,
    platform: str = "private_platform",
    area_id: str | None = "private_area",
    device_id: str | None = "private_device",
    registry: dict[str, object] | None = None,
    name: str = "Private display name",
) -> EntityModel:
    return EntityModel(
        entity_id=entity_id,
        name=name,
        domain="light",
        platform=platform,
        state="private_state",
        area_id=area_id,
        device_id=device_id,
        is_ignored=False,
        is_physical=True,
        registry=dict(
            registry
            if registry is not None
            else {
                "entity_id": entity_id,
                "platform": platform,
                "area_id": area_id,
                "device_id": device_id,
                "labels": ["private_label", "private_label"],
            }
        ),
    )


def _model(*entities: EntityModel, config: dict[str, object] | None = None) -> InstallationModel:
    return InstallationModel(
        areas={},
        devices={},
        entities={f"key-{index}": entity for index, entity in enumerate(entities)},
        integrations={},
        config=dict(config or {}),
        states=[],
        services=[],
        labels=[],
        raw={},
    )


def test_authoritative_normalized_facts_map_deterministically():
    candidates = build_relationship_candidates(_model(_entity()))

    assert [candidate.predicate for candidate in candidates] == [
        RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA,
        RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE,
        RelationshipPredicate.ENTITY_HAS_LABEL,
        RelationshipPredicate.ENTITY_USES_PLATFORM,
    ]
    assert all(candidate.persistence_eligible for candidate in candidates)
    assert {candidate.target_reference_contract for candidate in candidates} == {
        "ai001_loaded_component_observation_id_v1",
        "ca001_refh1_area_v1",
        "ca001_refh1_device_v1",
        "ca001_refh1_label_v1",
    }


def test_envelope_has_explicit_source_predicate_target_kind_and_target():
    candidate = build_relationship_candidates(_model(_entity()))[0]

    assert candidate.source_entity_identity_input == "light.private_kitchen"
    assert candidate.predicate is RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA
    assert candidate.target_kind is RelationshipTargetKind.AREA
    assert candidate.target_identity_input == "private_area"


def test_all_frozen_predicates_are_explicitly_directed():
    assert {
        candidate.direction
        for candidate in build_relationship_candidates(_model(_entity()))
    } == {RelationshipDirection.DIRECTED}


def test_reversing_directed_inputs_remains_distinct():
    forward = make_relationship_candidate(
        source_entity_identity_input="source-private",
        predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE,
        target_kind=RelationshipTargetKind.DEVICE,
        target_identity_input="target-private",
        evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_DEVICE,
    )
    reverse = make_relationship_candidate(
        source_entity_identity_input="target-private",
        predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE,
        target_kind=RelationshipTargetKind.DEVICE,
        target_identity_input="source-private",
        evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_DEVICE,
    )

    assert forward != reverse


def test_undirected_request_is_not_canonicalized_without_a_frozen_predicate():
    candidate = make_relationship_candidate(
        source_entity_identity_input="z-source-private",
        predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA,
        target_kind=RelationshipTargetKind.AREA,
        target_identity_input="a-target-private",
        evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_AREA,
        direction=RelationshipDirection.UNDIRECTED,
    )

    assert not candidate.persistence_eligible
    assert candidate.ineligibility_reason is RelationshipIneligibilityReason.UNSUPPORTED_DIRECTION
    assert candidate.source_entity_identity_input == "z-source-private"
    assert candidate.target_identity_input == "a-target-private"


def test_display_name_does_not_create_a_predicate():
    entity = _entity(
        registry={"entity_id": "light.private_kitchen", "platform": "private_platform"},
        area_id=None,
        device_id=None,
        name="Assigned to Device Area Label State Classification",
    )

    candidates = build_relationship_candidates(_model(entity))

    assert [candidate.predicate for candidate in candidates] == [
        RelationshipPredicate.ENTITY_USES_PLATFORM
    ]


def test_derived_area_is_deterministically_ineligible():
    entity = _entity(
        area_id="inherited_private_area",
        registry={
            "entity_id": "light.private_kitchen",
            "platform": "private_platform",
            "device_id": "private_device",
            "area_id": None,
        },
    )

    area = next(
        item
        for item in build_relationship_candidates(_model(entity))
        if item.predicate is RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA
    )

    assert not area.persistence_eligible
    assert area.ineligibility_reason is (
        RelationshipIneligibilityReason.INSUFFICIENT_AUTHORITATIVE_EVIDENCE
    )


def test_unsupported_target_kind_is_ineligible():
    candidate = make_relationship_candidate(
        source_entity_identity_input="source-private",
        predicate=RelationshipPredicate.ENTITY_USES_PLATFORM,
        target_kind=RelationshipTargetKind.STATE,
        target_identity_input="state-private",
        evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_PLATFORM,
    )

    assert not candidate.persistence_eligible
    assert candidate.ineligibility_reason is RelationshipIneligibilityReason.UNSUPPORTED_TARGET_KIND
    assert candidate.target_reference_contract is None


def test_raw_identifiers_are_absent_from_serialization_repr_and_errors():
    raw_values = {
        "light.private_kitchen",
        "private_platform",
        "private_device",
        "private_area",
        "private_label",
    }
    candidates = build_relationship_candidates(_model(_entity()))
    rendered = json.dumps(serialize_relationship_candidates(candidates), sort_keys=True)
    rendered += repr(candidates)

    for raw in raw_values:
        assert raw not in rendered

    with pytest.raises(ValueError) as error:
        NormalizedRelationshipCandidate(
            source_entity_identity_input="exception-source-private",
            predicate=RelationshipPredicate.ENTITY_HAS_LABEL,
            target_kind=RelationshipTargetKind.LABEL,
            target_identity_input="exception-target-private",
            direction=RelationshipDirection.DIRECTED,
            evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_LABEL,
            privacy_classification=candidates[0].privacy_classification,
            target_reference_contract="ca001_refh1_label_v1",
            persistence_eligible=True,
            ineligibility_reason=(
                RelationshipIneligibilityReason.INVALID_TARGET_IDENTITY_INPUT
            ),
        )
    assert "exception-source-private" not in str(error.value)
    assert "exception-target-private" not in str(error.value)


def test_duplicate_normalized_label_facts_collapse():
    entity = _entity(registry={
        "entity_id": "light.private_kitchen",
        "platform": "private_platform",
        "area_id": "private_area",
        "device_id": "private_device",
        "labels": ["cafe\N{COMBINING ACUTE ACCENT}", "caf\N{LATIN SMALL LETTER E WITH ACUTE}"],
    })
    candidates = build_relationship_candidates(_model(entity))

    assert sum(
        item.predicate is RelationshipPredicate.ENTITY_HAS_LABEL
        for item in candidates
    ) == 1


def test_input_order_does_not_change_candidate_order():
    first = _entity("light.first", registry={
        "entity_id": "light.first", "platform": "mqtt", "labels": []
    }, area_id=None, device_id=None, platform="mqtt")
    second = _entity("switch.second", registry={
        "entity_id": "switch.second", "platform": "zha", "labels": []
    }, area_id=None, device_id=None, platform="zha")

    assert build_relationship_candidates(_model(first, second)) == (
        build_relationship_candidates(_model(second, first))
    )


def test_existing_relationship_graph_and_analysis_inputs_are_not_mutated():
    model = _model(_entity())
    before = build_relationship_graph(model)

    build_relationship_candidates(model)

    assert build_relationship_graph(model) == before


def test_candidate_building_does_not_invoke_database_persistence(monkeypatch):
    from hadocs.application import operational_database

    def forbidden(*args, **kwargs):
        raise AssertionError("database persistence was invoked")

    monkeypatch.setattr(operational_database, "persist_operational_database", forbidden)
    assert build_relationship_candidates(_model(_entity()))


def test_operational_database_configuration_does_not_affect_contract_output():
    entity = _entity()
    disabled = build_relationship_candidates(_model(entity, config={}))
    enabled = build_relationship_candidates(
        _model(entity, config={"hask_database_enabled": True})
    )

    assert enabled == disabled
