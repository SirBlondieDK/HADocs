from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.hadocs.core.models import EntityModel
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
    "_ping",
    "_battery_replaced",
)

_EVENT_DEVICE_CLASSES = {
    "motion",
    "occupancy",
    "sound",
    "tamper",
    "vibration",
    "opening",
    "door",
    "window",
}


def interpret_entity_state(entity: EntityModel) -> StateInterpretation:
    """Interpret an entity state using its role and metadata."""

    state = normalize_text(entity.state)
    entity_id = normalize_text(entity.entity_id)
    domain = normalize_text(entity.domain)
    raw = entity.raw if isinstance(entity.raw, dict) else {}

    if entity.is_ignored:
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=100,
            reason="Entity is excluded by classification rules.",
        )

    disabled_by = normalize_text(raw.get("disabled_by"))
    if disabled_by:
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=100,
            reason=f"Entity is disabled by {disabled_by}.",
        )

    if state not in {"unknown", "unavailable"}:
        return StateInterpretation(
            meaning=StateMeaning.HEALTHY,
            fault_weight=0,
            confidence=95,
            reason=f"Entity has a normal state: {state or 'empty'}.",
        )

    if domain in {"button", "event"}:
        return StateInterpretation(
            meaning=StateMeaning.EXPECTED_UNKNOWN,
            fault_weight=0,
            confidence=100,
            reason=f"{domain} entities do not require a persistent state.",
        )

    if domain == "update":
        return StateInterpretation(
            meaning=StateMeaning.IGNORED,
            fault_weight=0,
            confidence=95,
            reason="Update entities are not reachability signals.",
        )

    if entity_id.endswith(_EXPECTED_UNKNOWN_SUFFIXES):
        return StateInterpretation(
            meaning=StateMeaning.EXPECTED_UNKNOWN,
            fault_weight=0,
            confidence=95,
            reason="The entity is only populated when an action or hold is active.",
        )

    device_class = normalize_text(
        raw.get("device_class")
        or raw.get("original_device_class")
    )

    if state == "unknown" and device_class in _EVENT_DEVICE_CLASSES:
        return StateInterpretation(
            meaning=StateMeaning.EXPECTED_UNKNOWN,
            fault_weight=0,
            confidence=80,
            reason="Event-style binary sensors may be unknown while idle.",
        )

    if state == "unknown":
        return StateInterpretation(
            meaning=StateMeaning.TRANSIENT,
            fault_weight=1,
            confidence=35,
            reason="Unknown is a weak signal without supporting reachability evidence.",
        )

    return StateInterpretation(
        meaning=StateMeaning.FAULT,
        fault_weight=8 if entity.importance == "important" else 4,
        confidence=70 if entity.importance == "important" else 55,
        reason="Unavailable is a stronger fault signal than unknown.",
    )
