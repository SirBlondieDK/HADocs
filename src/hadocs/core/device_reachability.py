from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.hadocs.core.device_overrides import DeviceOverride, get_device_policy
from src.hadocs.core.models import DeviceModel, EntityModel
from src.hadocs.core.state_interpreter import (
    StateMeaning,
    interpret_entity_state,
)
from src.hadocs.intelligence.engine import profile_entity
from src.hadocs.intelligence.freshness import (
    FreshnessStatus,
    determine_entity_freshness,
)
from src.hadocs.intelligence.profiles import ProfileKind
from src.hadocs.utils.normalize import normalize_text


class ReachabilityStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    EXPECTED_OFFLINE = "expected_offline"
    EXTERNAL = "external"
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
        return self.status in {
            ReachabilityStatus.OFFLINE,
            ReachabilityStatus.EXPECTED_OFFLINE,
        }


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
    profile = profile_entity(entity)

    if profile.kind is ProfileKind.AVAILABILITY:
        return True

    entity_id = normalize_text(entity.entity_id)

    return any(
        part in entity_id
        for part in _REACHABILITY_ID_PARTS
    )


def _primary_entities(
    entities: list[EntityModel],
) -> list[EntityModel]:
    primary: list[EntityModel] = []

    for entity in entities:
        profile = profile_entity(entity)

        if (
            entity.is_physical
            and profile.affects_health
            and profile.kind is not ProfileKind.DIAGNOSTIC
            and not entity.is_ignored
        ):
            primary.append(entity)

    return primary


def _healthy_primary_entities(
    entities: list[EntityModel],
) -> list[EntityModel]:
    healthy: list[EntityModel] = []

    for entity in _primary_entities(entities):
        interpretation = interpret_entity_state(entity)
        freshness = determine_entity_freshness(entity)

        if (
            interpretation.meaning is StateMeaning.HEALTHY
            and freshness.status
            not in {
                FreshnessStatus.STALE,
                FreshnessStatus.VERY_STALE,
            }
        ):
            healthy.append(entity)

    return healthy


def _freshness_evidence(
    entities: list[EntityModel],
) -> tuple[
    list[tuple[EntityModel, FreshnessStatus]],
    list[tuple[EntityModel, FreshnessStatus]],
]:
    stale: list[tuple[EntityModel, FreshnessStatus]] = []
    very_stale: list[tuple[EntityModel, FreshnessStatus]] = []

    for entity in _primary_entities(entities):
        freshness = determine_entity_freshness(entity)

        if freshness.status is FreshnessStatus.VERY_STALE:
            very_stale.append((entity, freshness.status))
        elif freshness.status is FreshnessStatus.STALE:
            stale.append((entity, freshness.status))

    return stale, very_stale


def determine_device_reachability(
    device: DeviceModel,
    overrides: tuple[DeviceOverride, ...] = (),
) -> ReachabilityResult:
    """Determine device reachability from explicit and supporting evidence."""
    policy = get_device_policy(device, overrides)

    if policy.ownership == "external":
        return ReachabilityResult(
            status=ReachabilityStatus.EXTERNAL,
            confidence=100,
            reason="Device is marked as external and is not part of this installation"
            + (f": {policy.reason}" if policy.reason else "."),
            evidence=("ownership=external",),
        )

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
        if policy.expected_offline:
            return ReachabilityResult(
                status=ReachabilityStatus.EXPECTED_OFFLINE,
                confidence=100,
                reason="Device is intentionally offline by user override"
                + (f": {policy.reason}" if policy.reason else "."),
                evidence=tuple(explicit_offline),
            )
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
            reason=(
                "The device has healthy primary entities with current or "
                "unknown-age reports."
            ),
            evidence=evidence,
        )

    primary_entities = _primary_entities(relevant_entities)
    stale_entities, very_stale_entities = _freshness_evidence(
        relevant_entities
    )

    if (
        primary_entities
        and len(very_stale_entities) == len(primary_entities)
    ):
        evidence = tuple(
            f"{entity.entity_id}=very_stale"
            for entity, _ in very_stale_entities[:5]
        )

        if policy.expected_offline:
            return ReachabilityResult(
                status=ReachabilityStatus.EXPECTED_OFFLINE,
                confidence=100,
                reason="Device is intentionally offline by user override"
                + (f": {policy.reason}" if policy.reason else "."),
                evidence=evidence,
            )
        return ReachabilityResult(
            status=ReachabilityStatus.OFFLINE,
            confidence=85,
            reason=(
                "All usable primary entities are very stale. The device is "
                "likely abandoned, removed, or persistently offline."
            ),
            evidence=evidence,
        )

    interpretations = [
        interpret_entity_state(entity)
        for entity in primary_entities
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
        confidence = 80 if stale_entities or very_stale_entities else 65

        if policy.expected_offline:
            return ReachabilityResult(
                status=ReachabilityStatus.EXPECTED_OFFLINE,
                confidence=100,
                reason="Device is intentionally offline by user override"
                + (f": {policy.reason}" if policy.reason else "."),
                evidence=(),
            )
        return ReachabilityResult(
            status=ReachabilityStatus.OFFLINE,
            confidence=confidence,
            reason=(
                "All usable physical entity evidence indicates confirmed "
                "unavailability."
            ),
            evidence=tuple(
                f"{entity.entity_id}={status.value}"
                for entity, status in [
                    *very_stale_entities,
                    *stale_entities,
                ][:5]
            ),
        )

    if stale_entities or very_stale_entities:
        evidence = tuple(
            f"{entity.entity_id}={status.value}"
            for entity, status in [
                *very_stale_entities,
                *stale_entities,
            ][:5]
        )

        return ReachabilityResult(
            status=ReachabilityStatus.UNKNOWN,
            confidence=60,
            reason=(
                "The device has stale primary entities, but no explicit "
                "offline signal was found."
            ),
            evidence=evidence,
        )

    return ReachabilityResult(
        status=ReachabilityStatus.UNKNOWN,
        confidence=25,
        reason="No reliable reachability signal was found.",
        evidence=(),
    )
