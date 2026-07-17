from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.hadocs.core.models import EntityModel
from src.hadocs.intelligence.engine import profile_entity
from src.hadocs.intelligence.profiles import ProfileKind
from src.hadocs.utils.normalize import normalize_text


class StateMeaning(str, Enum):
    HEALTHY = "healthy"
    FAULT = "fault"
    EXPECTED_UNKNOWN = "expected_unknown"
    EXPECTED_UNAVAILABLE = "expected_unavailable"
    TRANSIENT = "transient"
    IGNORED = "ignored"


@dataclass(frozen=True, slots=True)
class StateInterpretation:
    meaning: StateMeaning
    fault_weight: int
    confidence: int
    reason: str

    @property
    def is_fault(self) -> bool:
        return self.meaning is StateMeaning.FAULT


_EXPECTED_UNKNOWN_SUFFIXES = (
    "_holding_until",
)


def _registry_metadata(entity: EntityModel) -> tuple[dict, dict]:
    registry = getattr(entity, "registry", None)
    if not isinstance(registry, dict):
        registry = {}

    raw = getattr(entity, "raw", None)
    if not isinstance(raw, dict):
        raw = {}

    return registry, raw


def interpret_entity_state(entity: EntityModel) -> StateInterpretation:
    """Interpret an entity state using its HIL entity profile."""

    state = normalize_text(entity.state)
    entity_id = normalize_text(entity.entity_id)
    registry, raw = _registry_metadata(entity)
    profile = profile_entity(entity)

    if entity.is_ignored:
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=100,
            reason="Entity is excluded by classification rules.",
        )

    disabled_by = normalize_text(
        registry.get("disabled_by")
        or raw.get("disabled_by")
    )
    if disabled_by:
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=100,
            reason=f"Entity is disabled by {disabled_by}.",
        )

    if profile.kind is ProfileKind.DIAGNOSTIC:
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=95,
            reason=profile.reason,
        )

    if state not in {"unknown", "unavailable"}:
        return StateInterpretation(
            meaning=StateMeaning.HEALTHY,
            fault_weight=0,
            confidence=95,
            reason=f"Entity has a normal state: {state or 'empty'}.",
        )

    if entity_id.endswith(_EXPECTED_UNKNOWN_SUFFIXES):
        return StateInterpretation(
            meaning=StateMeaning.EXPECTED_UNKNOWN,
            fault_weight=0,
            confidence=95,
            reason=(
                "The entity is only populated while a temporary hold "
                "or similar condition is active."
            ),
        )

    if (
        profile.expected_unknown
        or profile.kind is ProfileKind.EVENT
    ):
        meaning = (
            StateMeaning.EXPECTED_UNAVAILABLE
            if state == "unavailable"
            else StateMeaning.EXPECTED_UNKNOWN
        )

        return StateInterpretation(
            meaning=meaning,
            fault_weight=0,
            confidence=100 if profile.kind is ProfileKind.ACTION else 90,
            reason=profile.reason,
        )

    if profile.kind is ProfileKind.CONFIGURATION:
        return StateInterpretation(
            meaning=(
                StateMeaning.EXPECTED_UNAVAILABLE
                if state == "unavailable"
                else StateMeaning.EXPECTED_UNKNOWN
            ),
            fault_weight=0,
            confidence=85,
            reason=profile.reason,
        )

    if state == "unknown":
        return StateInterpretation(
            meaning=StateMeaning.TRANSIENT,
            fault_weight=1 if profile.affects_health else 0,
            confidence=35,
            reason=(
                "Unknown is a weak signal without supporting "
                "reachability evidence."
            ),
        )

    if not profile.affects_health:
        return StateInterpretation(
            meaning=StateMeaning.EXPECTED_UNAVAILABLE,
            fault_weight=0,
            confidence=80,
            reason=profile.reason,
        )

    if profile.kind is ProfileKind.AVAILABILITY:
        return StateInterpretation(
            meaning=StateMeaning.FAULT,
            fault_weight=10,
            confidence=85,
            reason="An availability entity is unavailable.",
        )

    if profile.kind is ProfileKind.CONTROL:
        return StateInterpretation(
            meaning=StateMeaning.FAULT,
            fault_weight=8 if entity.importance == "important" else 6,
            confidence=75 if entity.importance == "important" else 65,
            reason="A device control entity is unavailable.",
        )

    return StateInterpretation(
        meaning=StateMeaning.FAULT,
        fault_weight=8 if entity.importance == "important" else 4,
        confidence=70 if entity.importance == "important" else 55,
        reason="Unavailable is a stronger fault signal than unknown.",
    )