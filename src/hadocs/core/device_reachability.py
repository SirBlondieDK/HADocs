from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.hadocs.core.models import DeviceModel, EntityModel
from src.hadocs.core.state_interpreter import (
    StateMeaning,
    interpret_entity_state,
)
from src.hadocs.utils.normalize import normalize_text


class ReachabilityStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SLEEPING = "sleeping"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    status: ReachabilityStatus
    confidence: int
    reason: str
    evidence: tuple[str, ...] = ()

    @property
    def is_offline(self) -> bool:
        return self.status is ReachabilityStatus.OFFLINE


_OFFLINE_STATES = {
    "dead",
    "disconnected",
    "offline",
    "failed",
    "not_ready",
    "not ready",
}

_ONLINE_STATES = {
    "alive",
    "connected",
    "online",
    "ready",
    "available",
}

_SLEEPING_STATES = {
    "asleep",
    "sleeping",
}

_REACHABILITY_ID_PARTS = (
    "availability",
    "available",
    "connection_state",
    "connectivity",
    "connected",
    "device_status",
    "node_status",
    "online",
    "reachable",
    "reachability",
)


def _is_reachability_entity(entity: EntityModel) -> bool:
    entity_id = normalize_text(entity.entity_id)

    return any(
        part in entity_id
        for part in _REACHABILITY_ID_PARTS
    )


def _healthy_primary_entities(
    entities: list[EntityModel],
) -> list[EntityModel]:
    healthy = []

    for entity in entities:
        interpretation = interpret_entity_state(entity)

        if (
            entity.is_physical
            and not entity.is_ignored
            and entity.importance != "diagnostic"
            and interpretation.meaning is StateMeaning.HEALTHY
        ):
            healthy.append(entity)

    return healthy


def determine_device_reachability(
    device: DeviceModel,
) -> ReachabilityResult:
    """Determine device reachability from explicit and supporting evidence."""

    explicit_online: list[str] = []
    explicit_offline: list[str] = []
    explicit_sleeping: list[str] = []

    relevant_entities = [
        entity
        for entity in device.entities
        if not entity.is_ignored
    ]

    for entity in relevant_entities:
        if not _is_reachability_entity(entity):
            continue

        state = normalize_text(entity.state)
        evidence = f"{entity.entity_id}={state or 'empty'}"

        if state in _OFFLINE_STATES:
            explicit_offline.append(evidence)
        elif state in _ONLINE_STATES:
            explicit_online.append(evidence)
        elif state in _SLEEPING_STATES:
            explicit_sleeping.append(evidence)
        elif entity.domain == "binary_sensor":
            if state == "off":
                explicit_offline.append(evidence)
            elif state == "on":
                explicit_online.append(evidence)

    if explicit_offline:
        return ReachabilityResult(
            status=ReachabilityStatus.OFFLINE,
            confidence=95,
            reason="An explicit reachability entity reports the device offline.",
            evidence=tuple(explicit_offline),
        )

    if explicit_online:
        return ReachabilityResult(
            status=ReachabilityStatus.ONLINE,
            confidence=95,
            reason="An explicit reachability entity reports the device online.",
            evidence=tuple(explicit_online),
        )

    if explicit_sleeping:
        return ReachabilityResult(
            status=ReachabilityStatus.SLEEPING,
            confidence=90,
            reason="An explicit status entity reports that the device is sleeping.",
            evidence=tuple(explicit_sleeping),
        )

    healthy_entities = _healthy_primary_entities(relevant_entities)

    if healthy_entities:
        evidence = tuple(
            f"{entity.entity_id}={normalize_text(entity.state)}"
            for entity in healthy_entities[:5]
        )

        return ReachabilityResult(
            status=ReachabilityStatus.ONLINE,
            confidence=70,
            reason="The device has healthy active physical entities.",
            evidence=evidence,
        )

    interpretations = [
        interpret_entity_state(entity)
        for entity in relevant_entities
        if entity.is_physical
    ]

    confirmed_faults = [
        interpretation
        for interpretation in interpretations
        if interpretation.meaning is StateMeaning.FAULT
    ]

    non_faults = [
        interpretation
        for interpretation in interpretations
        if interpretation.meaning
        in {
            StateMeaning.HEALTHY,
            StateMeaning.EXPECTED_UNKNOWN,
            StateMeaning.EXPECTED_UNAVAILABLE,
            StateMeaning.TRANSIENT,
        }
    ]

    if confirmed_faults and not non_faults:
        return ReachabilityResult(
            status=ReachabilityStatus.OFFLINE,
            confidence=65,
            reason=(
                "All usable physical entity evidence indicates "
                "confirmed unavailability."
            ),
            evidence=(),
        )

    return ReachabilityResult(
        status=ReachabilityStatus.UNKNOWN,
        confidence=25,
        reason="No reliable reachability signal was found.",
        evidence=(),
    )
