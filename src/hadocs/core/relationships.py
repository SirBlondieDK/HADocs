from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping
import unicodedata

from hadocs.core.models import HADocsModel, DeviceModel, EntityModel, IntegrationModel
from hadocs.core.entity_eligibility import is_disabled_entity


class RelationshipPredicate(str, Enum):
    ENTITY_USES_PLATFORM = "entity_uses_platform"
    ENTITY_ASSIGNED_TO_DEVICE = "entity_assigned_to_device"
    ENTITY_ASSIGNED_TO_AREA = "entity_assigned_to_area"
    ENTITY_HAS_LABEL = "entity_has_label"


class RelationshipTargetKind(str, Enum):
    ENTITY = "entity"
    DEVICE = "device"
    AREA = "area"
    LABEL = "label"
    INTEGRATION = "integration"
    STATE = "state"
    CLASSIFICATION = "classification"


class RelationshipDirection(str, Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


class RelationshipEvidenceOrigin(str, Enum):
    ENTITY_REGISTRY_PLATFORM = "entity_registry.platform"
    ENTITY_REGISTRY_DEVICE = "entity_registry.device_id"
    ENTITY_REGISTRY_AREA = "entity_registry.area_id"
    ENTITY_REGISTRY_LABEL = "entity_registry.labels"
    NORMALIZED_DERIVATION = "normalized_derivation"
    AMBIGUOUS_INPUT = "ambiguous_input"


class RelationshipPrivacyClassification(str, Enum):
    PROTECTED_STRUCTURAL_REFERENCE = "protected_structural_reference"


class RelationshipIneligibilityReason(str, Enum):
    INVALID_SOURCE_IDENTITY_INPUT = "invalid_source_identity_input"
    INVALID_TARGET_IDENTITY_INPUT = "invalid_target_identity_input"
    INSUFFICIENT_AUTHORITATIVE_EVIDENCE = "insufficient_authoritative_evidence"
    UNSUPPORTED_DIRECTION = "unsupported_direction"
    UNSUPPORTED_TARGET_KIND = "unsupported_target_kind"
    MISSING_TARGET_REFERENCE_CONTRACT = "missing_target_reference_contract"


TARGET_REFERENCE_CONTRACTS: Mapping[RelationshipTargetKind, str] = MappingProxyType(
    {
        RelationshipTargetKind.ENTITY: "ca001_refh1_entity_v1",
        RelationshipTargetKind.DEVICE: "ca001_refh1_device_v1",
        RelationshipTargetKind.AREA: "ca001_refh1_area_v1",
        RelationshipTargetKind.LABEL: "ca001_refh1_label_v1",
        RelationshipTargetKind.INTEGRATION: "ai001_loaded_component_observation_id_v1",
    }
)


@dataclass(frozen=True, slots=True)
class RelationshipPredicatePolicy:
    predicate: RelationshipPredicate
    meaning: str
    source_kind: str
    target_kind: RelationshipTargetKind
    direction: RelationshipDirection
    evidence_origin: RelationshipEvidenceOrigin
    privacy_classification: RelationshipPrivacyClassification
    target_reference_contract: str


RELATIONSHIP_PREDICATE_POLICIES: Mapping[
    RelationshipPredicate, RelationshipPredicatePolicy
] = MappingProxyType(
    {
        RelationshipPredicate.ENTITY_USES_PLATFORM: RelationshipPredicatePolicy(
            predicate=RelationshipPredicate.ENTITY_USES_PLATFORM,
            meaning="an entity explicitly declares the platform that provides it",
            source_kind="entity",
            target_kind=RelationshipTargetKind.INTEGRATION,
            direction=RelationshipDirection.DIRECTED,
            evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_PLATFORM,
            privacy_classification=(
                RelationshipPrivacyClassification.PROTECTED_STRUCTURAL_REFERENCE
            ),
            target_reference_contract="ai001_loaded_component_observation_id_v1",
        ),
        RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE: RelationshipPredicatePolicy(
            predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE,
            meaning="an entity registry entry explicitly assigns the entity to a device",
            source_kind="entity",
            target_kind=RelationshipTargetKind.DEVICE,
            direction=RelationshipDirection.DIRECTED,
            evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_DEVICE,
            privacy_classification=(
                RelationshipPrivacyClassification.PROTECTED_STRUCTURAL_REFERENCE
            ),
            target_reference_contract="ca001_refh1_device_v1",
        ),
        RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA: RelationshipPredicatePolicy(
            predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA,
            meaning="an entity registry entry explicitly assigns the entity to an area",
            source_kind="entity",
            target_kind=RelationshipTargetKind.AREA,
            direction=RelationshipDirection.DIRECTED,
            evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_AREA,
            privacy_classification=(
                RelationshipPrivacyClassification.PROTECTED_STRUCTURAL_REFERENCE
            ),
            target_reference_contract="ca001_refh1_area_v1",
        ),
        RelationshipPredicate.ENTITY_HAS_LABEL: RelationshipPredicatePolicy(
            predicate=RelationshipPredicate.ENTITY_HAS_LABEL,
            meaning="an entity registry entry explicitly assigns a label to the entity",
            source_kind="entity",
            target_kind=RelationshipTargetKind.LABEL,
            direction=RelationshipDirection.DIRECTED,
            evidence_origin=RelationshipEvidenceOrigin.ENTITY_REGISTRY_LABEL,
            privacy_classification=(
                RelationshipPrivacyClassification.PROTECTED_STRUCTURAL_REFERENCE
            ),
            target_reference_contract="ca001_refh1_label_v1",
        ),
    }
)


@dataclass(frozen=True, slots=True)
class NormalizedRelationshipCandidate:
    """In-memory relationship fact awaiting protected endpoint derivation."""

    source_entity_identity_input: str = field(repr=False)
    predicate: RelationshipPredicate
    target_kind: RelationshipTargetKind
    target_identity_input: str | None = field(repr=False)
    direction: RelationshipDirection
    evidence_origin: RelationshipEvidenceOrigin
    privacy_classification: RelationshipPrivacyClassification
    target_reference_contract: str | None
    persistence_eligible: bool
    ineligibility_reason: RelationshipIneligibilityReason | None

    def __post_init__(self) -> None:
        if self.persistence_eligible and self.ineligibility_reason is not None:
            raise ValueError("eligible relationship candidate cannot have a reason")
        if not self.persistence_eligible and self.ineligibility_reason is None:
            raise ValueError("ineligible relationship candidate requires a reason")

    def public_dict(self) -> dict[str, object]:
        """Serialize classification only; raw identity inputs stay private."""

        return {
            "source_kind": "entity",
            "source_identity": "transient_input_redacted",
            "predicate": self.predicate.value,
            "target_kind": self.target_kind.value,
            "target_identity": (
                "transient_input_redacted"
                if self.target_identity_input is not None
                else "unavailable"
            ),
            "direction": self.direction.value,
            "evidence_origin": self.evidence_origin.value,
            "privacy_classification": self.privacy_classification.value,
            "target_reference_contract": self.target_reference_contract,
            "persistence_eligible": self.persistence_eligible,
            "ineligibility_reason": (
                self.ineligibility_reason.value
                if self.ineligibility_reason is not None
                else None
            ),
        }


def _normalize_identity_input(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = unicodedata.normalize("NFC", value)
    if not normalized or any(
        ord(character) < 32 or ord(character) == 127
        for character in normalized
    ):
        return None
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return None
    return normalized


def make_relationship_candidate(
    *,
    source_entity_identity_input: object,
    predicate: RelationshipPredicate,
    target_kind: RelationshipTargetKind,
    target_identity_input: object,
    evidence_origin: RelationshipEvidenceOrigin,
    direction: RelationshipDirection | None = None,
) -> NormalizedRelationshipCandidate:
    """Classify one explicit candidate without deriving or exposing references."""

    policy = RELATIONSHIP_PREDICATE_POLICIES[predicate]
    actual_direction = direction or policy.direction
    target_reference_contract = TARGET_REFERENCE_CONTRACTS.get(target_kind)
    source = _normalize_identity_input(source_entity_identity_input) or ""
    target = _normalize_identity_input(target_identity_input)

    reason: RelationshipIneligibilityReason | None = None
    if not source:
        reason = RelationshipIneligibilityReason.INVALID_SOURCE_IDENTITY_INPUT
    elif target is None:
        reason = RelationshipIneligibilityReason.INVALID_TARGET_IDENTITY_INPUT
    elif target_kind is not policy.target_kind:
        reason = RelationshipIneligibilityReason.UNSUPPORTED_TARGET_KIND
    elif actual_direction is not policy.direction:
        reason = RelationshipIneligibilityReason.UNSUPPORTED_DIRECTION
    elif evidence_origin is not policy.evidence_origin:
        reason = RelationshipIneligibilityReason.INSUFFICIENT_AUTHORITATIVE_EVIDENCE
    elif not target_reference_contract:
        reason = RelationshipIneligibilityReason.MISSING_TARGET_REFERENCE_CONTRACT

    return NormalizedRelationshipCandidate(
        source_entity_identity_input=source,
        predicate=predicate,
        target_kind=target_kind,
        target_identity_input=target,
        direction=actual_direction,
        evidence_origin=evidence_origin,
        privacy_classification=policy.privacy_classification,
        target_reference_contract=target_reference_contract,
        persistence_eligible=reason is None,
        ineligibility_reason=reason,
    )


def _registry_evidence(
    entity: EntityModel,
    field_name: str,
    normalized_value: object,
    explicit_origin: RelationshipEvidenceOrigin,
) -> RelationshipEvidenceOrigin:
    registry_value = entity.registry.get(field_name)
    if (
        isinstance(normalized_value, str)
        and normalized_value
        and isinstance(registry_value, str)
        and registry_value == normalized_value
    ):
        return explicit_origin
    return RelationshipEvidenceOrigin.NORMALIZED_DERIVATION


def build_relationship_candidates(
    model: HADocsModel,
) -> tuple[NormalizedRelationshipCandidate, ...]:
    """Extract only frozen relationship predicates from normalized entity facts."""

    candidates: set[NormalizedRelationshipCandidate] = set()
    for entity in model.entities.values():
        source = entity.entity_id
        candidates.add(
            make_relationship_candidate(
                source_entity_identity_input=source,
                predicate=RelationshipPredicate.ENTITY_USES_PLATFORM,
                target_kind=RelationshipTargetKind.INTEGRATION,
                target_identity_input=entity.platform,
                evidence_origin=_registry_evidence(
                    entity,
                    "platform",
                    entity.platform,
                    RelationshipEvidenceOrigin.ENTITY_REGISTRY_PLATFORM,
                ),
            )
        )

        if entity.device_id is not None:
            candidates.add(
                make_relationship_candidate(
                    source_entity_identity_input=source,
                    predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_DEVICE,
                    target_kind=RelationshipTargetKind.DEVICE,
                    target_identity_input=entity.device_id,
                    evidence_origin=_registry_evidence(
                        entity,
                        "device_id",
                        entity.device_id,
                        RelationshipEvidenceOrigin.ENTITY_REGISTRY_DEVICE,
                    ),
                )
            )

        if entity.area_id is not None:
            candidates.add(
                make_relationship_candidate(
                    source_entity_identity_input=source,
                    predicate=RelationshipPredicate.ENTITY_ASSIGNED_TO_AREA,
                    target_kind=RelationshipTargetKind.AREA,
                    target_identity_input=entity.area_id,
                    evidence_origin=_registry_evidence(
                        entity,
                        "area_id",
                        entity.area_id,
                        RelationshipEvidenceOrigin.ENTITY_REGISTRY_AREA,
                    ),
                )
            )

        labels = entity.registry.get("labels", ())
        label_values = labels if isinstance(labels, (list, tuple, set)) else (labels,)
        for label in label_values:
            candidates.add(
                make_relationship_candidate(
                    source_entity_identity_input=source,
                    predicate=RelationshipPredicate.ENTITY_HAS_LABEL,
                    target_kind=RelationshipTargetKind.LABEL,
                    target_identity_input=label,
                    evidence_origin=(
                        RelationshipEvidenceOrigin.ENTITY_REGISTRY_LABEL
                        if isinstance(labels, (list, tuple, set))
                        else RelationshipEvidenceOrigin.AMBIGUOUS_INPUT
                    ),
                )
            )

    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.predicate.value.encode("utf-8"),
                item.source_entity_identity_input.encode("utf-8"),
                item.target_kind.value.encode("utf-8"),
                (item.target_identity_input or "").encode("utf-8"),
                item.evidence_origin.value.encode("utf-8"),
            ),
        )
    )


def serialize_relationship_candidates(
    candidates: tuple[NormalizedRelationshipCandidate, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(candidate.public_dict() for candidate in candidates)


@dataclass
class EntityRelationship:
    entity_id: str
    name: str
    domain: str
    state: str
    area_id: str | None
    device_id: str | None
    device_name: str
    integration: str
    importance: str
    is_ignored: bool


@dataclass
class DeviceRelationship:
    device_id: str
    name: str
    area_id: str | None
    classification: str
    integrations: list[str] = field(default_factory=list)
    important_entities: list[str] = field(default_factory=list)
    diagnostic_entities: list[str] = field(default_factory=list)
    ignored_entities: list[str] = field(default_factory=list)
    problem_entities: list[str] = field(default_factory=list)


@dataclass
class IntegrationRelationship:
    platform: str
    devices: list[str] = field(default_factory=list)
    important_entities: list[str] = field(default_factory=list)
    diagnostic_entities: list[str] = field(default_factory=list)
    ignored_entities: list[str] = field(default_factory=list)
    problem_entities: list[str] = field(default_factory=list)


@dataclass
class RelationshipGraph:
    entities: dict[str, EntityRelationship]
    devices: dict[str, DeviceRelationship]
    integrations: dict[str, IntegrationRelationship]


def build_relationship_graph(model: HADocsModel) -> RelationshipGraph:
    entity_relations: dict[str, EntityRelationship] = {}
    device_relations: dict[str, DeviceRelationship] = {}
    integration_relations: dict[str, IntegrationRelationship] = {}

    for device in model.devices.values():
        integrations = sorted({entity.platform for entity in device.entities})
        important = sorted(entity.entity_id for entity in device.entities if entity.importance == "important")
        diagnostic = sorted(entity.entity_id for entity in device.entities if entity.importance == "diagnostic")
        ignored = sorted(entity.entity_id for entity in device.entities if entity.is_ignored)
        problems = sorted(
            entity.entity_id
            for entity in device.entities
            if entity.state in ("unknown", "unavailable")
            and not entity.is_ignored
            and entity.importance != "diagnostic"
            and not is_disabled_entity(entity)
        )

        device_relations[device.device_id] = DeviceRelationship(
            device_id=device.device_id,
            name=device.name,
            area_id=device.area_id,
            classification=device.classification,
            integrations=integrations,
            important_entities=important,
            diagnostic_entities=diagnostic,
            ignored_entities=ignored,
            problem_entities=problems,
        )

    for entity in model.entities.values():
        device = model.devices.get(entity.device_id or "")
        entity_relations[entity.entity_id] = EntityRelationship(
            entity_id=entity.entity_id,
            name=entity.name,
            domain=entity.domain,
            state=entity.state,
            area_id=entity.area_id,
            device_id=entity.device_id,
            device_name=device.name if device else "",
            integration=entity.platform,
            importance=entity.importance,
            is_ignored=entity.is_ignored,
        )

    for integration in model.integrations.values():
        devices = sorted({device.name for device in integration.devices})
        important = sorted(entity.entity_id for entity in integration.entities if entity.importance == "important")
        diagnostic = sorted(entity.entity_id for entity in integration.entities if entity.importance == "diagnostic")
        ignored = sorted(entity.entity_id for entity in integration.entities if entity.is_ignored)
        problems = sorted(
            entity.entity_id
            for entity in integration.entities
            if entity.state in ("unknown", "unavailable")
            and not entity.is_ignored
            and entity.importance != "diagnostic"
            and not is_disabled_entity(entity)
        )

        integration_relations[integration.platform] = IntegrationRelationship(
            platform=integration.platform,
            devices=devices,
            important_entities=important,
            diagnostic_entities=diagnostic,
            ignored_entities=ignored,
            problem_entities=problems,
        )

    return RelationshipGraph(
        entities=entity_relations,
        devices=device_relations,
        integrations=integration_relations,
    )


def top_problem_devices(graph: RelationshipGraph, limit: int = 20) -> list[DeviceRelationship]:
    devices = sorted(
        graph.devices.values(),
        key=lambda device: len(device.problem_entities),
        reverse=True,
    )
    return [device for device in devices if device.problem_entities][:limit]


def top_problem_integrations(graph: RelationshipGraph, limit: int = 20) -> list[IntegrationRelationship]:
    integrations = sorted(
        graph.integrations.values(),
        key=lambda integration: len(integration.problem_entities),
        reverse=True,
    )
    return [integration for integration in integrations if integration.problem_entities][:limit]
