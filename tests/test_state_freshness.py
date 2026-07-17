from datetime import datetime, timezone

from src.hadocs.core.models import EntityModel
from src.hadocs.intelligence.freshness import (
    FreshnessStatus,
    determine_entity_freshness,
)


NOW = datetime(2026, 7, 16, 18, 0, 0, tzinfo=timezone.utc)


def make_entity(
    *,
    last_reported: str | None = None,
    last_updated: str | None = None,
    last_changed: str | None = None,
) -> EntityModel:
    return EntityModel(
        entity_id="sensor.test",
        name="Test",
        domain="sensor",
        platform="test",
        state="21.5",
        area_id=None,
        device_id=None,
        is_ignored=False,
        is_physical=True,
        last_reported=last_reported,
        last_updated=last_updated,
        last_changed=last_changed,
    )


def test_freshness_prefers_last_reported():
    entity = make_entity(
        last_reported="2026-07-16T17:55:00+00:00",
        last_updated="2026-07-10T12:00:00+00:00",
        last_changed="2026-07-01T12:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH
    assert result.timestamp_source == "last_reported"
    assert result.age_seconds == 300


def test_stable_value_can_be_fresh_even_when_last_changed_is_old():
    entity = make_entity(
        last_reported="2026-07-16T17:59:00+00:00",
        last_changed="2026-01-01T00:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH
    assert result.timestamp_source == "last_reported"


def test_last_updated_is_used_when_last_reported_is_missing():
    entity = make_entity(
        last_updated="2026-07-16T17:30:00+00:00",
        last_changed="2026-07-01T00:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH
    assert result.timestamp_source == "last_updated"


def test_last_changed_is_only_a_final_fallback():
    entity = make_entity(
        last_changed="2026-07-16T17:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH
    assert result.timestamp_source == "last_changed"


def test_missing_timestamps_are_unknown_not_stale():
    result = determine_entity_freshness(
        make_entity(),
        now=NOW,
    )

    assert result.status is FreshnessStatus.UNKNOWN
    assert result.age_seconds is None
    assert result.is_stale is False


def test_six_hours_old_is_aging():
    entity = make_entity(
        last_reported="2026-07-16T11:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.AGING
    assert result.is_stale is False


def test_two_days_old_is_stale():
    entity = make_entity(
        last_reported="2026-07-14T12:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.STALE
    assert result.is_stale is True


def test_one_year_old_is_very_stale():
    entity = make_entity(
        last_reported="2025-07-16T18:00:00+00:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.VERY_STALE
    assert result.confidence == 95


def test_z_suffix_is_supported():
    entity = make_entity(
        last_reported="2026-07-16T17:59:00Z",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH


def test_invalid_timestamp_is_unknown():
    entity = make_entity(
        last_reported="not-a-date",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.UNKNOWN


def test_naive_timestamp_is_treated_as_utc():
    entity = make_entity(
        last_reported="2026-07-16T17:59:00",
    )

    result = determine_entity_freshness(entity, now=NOW)

    assert result.status is FreshnessStatus.FRESH
    assert result.age_seconds == 60
