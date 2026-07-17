from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.hadocs.core.device_overrides import DeviceOverride, get_device_policy
from src.hadocs.core.device_reachability import (
    ReachabilityStatus,
    determine_device_reachability,
)
from src.hadocs.core.models import (
    DeviceModel,
    EntityModel,
    InstallationModel,
)
from src.hadocs.intelligence.engine import profile_entity
from src.hadocs.intelligence.freshness import (
    FreshnessStatus,
    determine_entity_freshness,
)
from src.hadocs.intelligence.profiles import ProfileKind


class IntegrationHealthStatus(str, Enum):
    HEALTHY = "healthy"
    MAINTENANCE = "maintenance"
    WARNING = "warning"
    PROBLEM = "problem"


@dataclass(frozen=True, slots=True)
class IntegrationHealth:
    platform: str
    score: int
    status: IntegrationHealthStatus

    total_entities: int
    total_devices: int
    physical_devices: int

    online_devices: int
    offline_devices: int
    sleeping_devices: int
    unknown_devices: int
    expected_offline_devices: int
    external_devices: int

    fresh_devices: int
    aging_devices: int
    stale_devices: int
    very_stale_devices: int
    unknown_freshness_devices: int

    explicit_offline_devices: tuple[str, ...] = ()
    probable_offline_devices: tuple[str, ...] = ()
    intentionally_offline_devices: tuple[str, ...] = ()
    external_device_names: tuple[str, ...] = ()
    stale_device_names: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def _primary_entities(device: DeviceModel) -> list[EntityModel]:
    entities: list[EntityModel] = []

    for entity in device.entities:
        profile = profile_entity(entity)

        if (
            entity.is_physical
            and not entity.is_ignored
            and profile.affects_health
            and profile.kind is not ProfileKind.DIAGNOSTIC
        ):
            entities.append(entity)

    return entities


def _device_freshness(
    device: DeviceModel,
    *,
    now: datetime | None = None,
) -> FreshnessStatus:
    """Summarize freshness without treating missing timestamps as failure."""

    primary_entities = _primary_entities(device)

    if not primary_entities:
        return FreshnessStatus.UNKNOWN

    statuses = [
        determine_entity_freshness(entity, now=now).status
        for entity in primary_entities
    ]

    if FreshnessStatus.FRESH in statuses:
        return FreshnessStatus.FRESH

    if FreshnessStatus.AGING in statuses:
        return FreshnessStatus.AGING

    known_statuses = [
        status
        for status in statuses
        if status is not FreshnessStatus.UNKNOWN
    ]

    if not known_statuses:
        return FreshnessStatus.UNKNOWN

    if all(
        status is FreshnessStatus.VERY_STALE
        for status in known_statuses
    ):
        return FreshnessStatus.VERY_STALE

    if all(
        status in {
            FreshnessStatus.STALE,
            FreshnessStatus.VERY_STALE,
        }
        for status in known_statuses
    ):
        return FreshnessStatus.STALE

    return FreshnessStatus.UNKNOWN


def _unique_devices(
    devices: list[DeviceModel],
) -> list[DeviceModel]:
    unique: dict[str, DeviceModel] = {}

    for device in devices:
        unique.setdefault(device.device_id, device)

    return list(unique.values())


def _status_from_score(
    score: int,
    *,
    stale_devices: int,
    very_stale_devices: int,
) -> IntegrationHealthStatus:
    if score < 60:
        return IntegrationHealthStatus.PROBLEM

    if score < 85:
        return IntegrationHealthStatus.WARNING

    if stale_devices or very_stale_devices:
        return IntegrationHealthStatus.MAINTENANCE

    return IntegrationHealthStatus.HEALTHY


def calculate_integration_health(
    model: InstallationModel,
    *,
    now: datetime | None = None,
    overrides: tuple[DeviceOverride, ...] = (),
) -> list[IntegrationHealth]:
    """Calculate integration health from devices, not raw entity-state counts."""

    results: list[IntegrationHealth] = []

    for integration in model.integrations.values():
        devices = _unique_devices(list(integration.devices))
        all_physical_devices = [
            device
            for device in devices
            if device.is_physical
        ]
        external_device_names = [
            device.name
            for device in all_physical_devices
            if get_device_policy(device, overrides, now).ownership == "external"
        ]
        physical_devices = [
            device
            for device in all_physical_devices
            if get_device_policy(device, overrides, now).ownership != "external"
        ]

        online = 0
        offline = 0
        sleeping = 0
        unknown = 0
        expected_offline = 0
        external = len(external_device_names)

        fresh = 0
        aging = 0
        stale = 0
        very_stale = 0
        unknown_freshness = 0

        explicit_offline_names: list[str] = []
        probable_offline_names: list[str] = []
        expected_offline_names: list[str] = []
        stale_names: list[str] = []

        explicit_offline_count = 0
        probable_offline_count = 0

        for device in physical_devices:
            policy = get_device_policy(device, overrides, now)
            reachability = determine_device_reachability(device, overrides)
            freshness = (
                FreshnessStatus.UNKNOWN
                if policy.ignore_stale or policy.expected_offline
                else _device_freshness(device, now=now)
            )

            # A device that only looks offline because every primary entity is
            # very stale is a maintenance case, not an active outage. This is
            # common for retired phones, tablets and abandoned integrations.
            stale_only_offline = (
                reachability.status is ReachabilityStatus.OFFLINE
                and reachability.confidence < 90
                and freshness is FreshnessStatus.VERY_STALE
            )

            if reachability.status is ReachabilityStatus.ONLINE:
                online += 1
            elif reachability.status is ReachabilityStatus.EXPECTED_OFFLINE:
                expected_offline += 1
                expected_offline_names.append(device.name)
            elif reachability.status is ReachabilityStatus.OFFLINE:
                if stale_only_offline:
                    unknown += 1
                else:
                    offline += 1

                    if reachability.confidence >= 90:
                        explicit_offline_count += 1
                        explicit_offline_names.append(device.name)
                    else:
                        probable_offline_count += 1
                        probable_offline_names.append(device.name)
            elif reachability.status is ReachabilityStatus.SLEEPING:
                sleeping += 1
            else:
                unknown += 1

            if freshness is FreshnessStatus.FRESH:
                fresh += 1
            elif freshness is FreshnessStatus.AGING:
                aging += 1
            elif freshness is FreshnessStatus.STALE:
                stale += 1
                stale_names.append(device.name)
            elif freshness is FreshnessStatus.VERY_STALE:
                very_stale += 1
                stale_names.append(device.name)
            else:
                unknown_freshness += 1

        score = 100

        # Explicit outages are authoritative and receive the strongest penalty.
        score -= min(60, explicit_offline_count * 30)

        # Probable active outages matter, but are weaker than explicit signals.
        score -= min(40, probable_offline_count * 15)

        # Staleness is primarily a maintenance signal.
        score -= min(10, stale * 2)
        score -= min(20, very_stale * 5)

        # Unknown reachability is deliberately not penalized. Unknown means
        # insufficient evidence, not failure. This also prevents action-only
        # and stateless integrations from losing health points.
        score = max(0, min(100, score))

        reasons: list[str] = []

        if explicit_offline_count:
            reasons.append(
                f"{explicit_offline_count} physical device(s) have explicit "
                "offline evidence."
            )

        if probable_offline_count:
            reasons.append(
                f"{probable_offline_count} physical device(s) are probably "
                "offline."
            )

        if very_stale:
            reasons.append(
                f"{very_stale} physical device(s) have only very stale "
                "primary reports."
            )

        if stale:
            reasons.append(
                f"{stale} physical device(s) have stale primary reports."
            )

        if external:
            reasons.append(
                f"{external} discovered device(s) are marked external and "
                "were excluded from health scoring."
            )

        if expected_offline:
            reasons.append(
                f"{expected_offline} device(s) are intentionally offline "
                "by user override and received no outage penalty."
            )

        if sleeping:
            reasons.append(
                f"{sleeping} sleeping device(s) were treated as healthy "
                "protocol behavior."
            )

        if not reasons:
            if physical_devices:
                reasons.append(
                    "No evidence-based device outages or stale-device "
                    "maintenance issues were found."
                )
            else:
                reasons.append(
                    "This integration has no physical devices requiring a "
                    "device-health score."
                )

        status = _status_from_score(
            score,
            stale_devices=stale,
            very_stale_devices=very_stale,
        )

        results.append(
            IntegrationHealth(
                platform=integration.platform,
                score=score,
                status=status,
                total_entities=len(integration.entities),
                total_devices=len(devices),
                physical_devices=len(physical_devices),
                online_devices=online,
                offline_devices=offline,
                sleeping_devices=sleeping,
                unknown_devices=unknown,
                expected_offline_devices=expected_offline,
                external_devices=external,
                fresh_devices=fresh,
                aging_devices=aging,
                stale_devices=stale,
                very_stale_devices=very_stale,
                unknown_freshness_devices=unknown_freshness,
                explicit_offline_devices=tuple(
                    sorted(explicit_offline_names)
                ),
                probable_offline_devices=tuple(
                    sorted(probable_offline_names)
                ),
                intentionally_offline_devices=tuple(sorted(expected_offline_names)),
                external_device_names=tuple(sorted(external_device_names)),
                stale_device_names=tuple(sorted(set(stale_names))),
                reasons=tuple(reasons),
            )
        )

    return sorted(
        results,
        key=lambda item: (
            item.score,
            item.platform.lower(),
        ),
    )
