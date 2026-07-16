from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from src.hadocs.core.models import EntityModel


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    VERY_STALE = "very_stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FreshnessResult:
    status: FreshnessStatus
    age_seconds: int | None
    confidence: int
    reason: str
    timestamp_source: str | None = None

    @property
    def is_stale(self) -> bool:
        return self.status in {
            FreshnessStatus.STALE,
            FreshnessStatus.VERY_STALE,
        }


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None

    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _best_timestamp(entity: EntityModel) -> tuple[datetime | None, str | None]:
    candidates = (
        ("last_reported", getattr(entity, "last_reported", None)),
        ("last_updated", getattr(entity, "last_updated", None)),
        ("last_changed", getattr(entity, "last_changed", None)),
    )

    for source, value in candidates:
        parsed = _parse_timestamp(value)
        if parsed is not None:
            return parsed, source

    return None, None


def determine_entity_freshness(
    entity: EntityModel,
    *,
    now: datetime | None = None,
    aging_after_seconds: int = 6 * 60 * 60,
    stale_after_seconds: int = 24 * 60 * 60,
    very_stale_after_seconds: int = 30 * 24 * 60 * 60,
) -> FreshnessResult:
    """Classify entity freshness from Home Assistant state timestamps.

    Timestamp priority:
    1. last_reported
    2. last_updated
    3. last_changed

    A missing timestamp never proves that an entity is stale.
    """

    timestamp, source = _best_timestamp(entity)

    if timestamp is None:
        return FreshnessResult(
            status=FreshnessStatus.UNKNOWN,
            age_seconds=None,
            confidence=20,
            reason="No usable Home Assistant state timestamp is available.",
            timestamp_source=None,
        )

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    age_seconds = max(0, int((current - timestamp).total_seconds()))

    if age_seconds >= very_stale_after_seconds:
        return FreshnessResult(
            status=FreshnessStatus.VERY_STALE,
            age_seconds=age_seconds,
            confidence=95,
            reason=(
                "The entity has not reported for a very long time and is "
                "likely an abandoned, removed, or persistently offline source."
            ),
            timestamp_source=source,
        )

    if age_seconds >= stale_after_seconds:
        return FreshnessResult(
            status=FreshnessStatus.STALE,
            age_seconds=age_seconds,
            confidence=85,
            reason=(
                "The entity has not reported within the configured stale "
                "window."
            ),
            timestamp_source=source,
        )

    if age_seconds >= aging_after_seconds:
        return FreshnessResult(
            status=FreshnessStatus.AGING,
            age_seconds=age_seconds,
            confidence=60,
            reason=(
                "The entity report is older than normal, but this alone does "
                "not prove that the device is offline."
            ),
            timestamp_source=source,
        )

    return FreshnessResult(
        status=FreshnessStatus.FRESH,
        age_seconds=age_seconds,
        confidence=90,
        reason="The entity has reported recently.",
        timestamp_source=source,
    )
