from datetime import UTC, datetime
from types import SimpleNamespace

from src.hadocs.core.device_overrides import (
    get_device_policy,
    override_from_mapping,
)


def device(device_id="dev-1"):
    return SimpleNamespace(device_id=device_id, name="Test", entities=[])


def test_nested_power_controlled_policy_is_expected_offline():
    override = override_from_mapping({
        "device_id": "dev-1",
        "policy": {
            "ownership": "owned",
            "purpose": "automation",
            "type": "power_controlled",
        },
    })
    policy = get_device_policy(device(), (override,))
    assert policy.policy_type == "power_controlled"
    assert policy.expected_offline is True
    assert policy.purpose == "automation"


def test_seasonal_policy_is_expected_offline_outside_active_months():
    override = override_from_mapping({
        "device_id": "dev-1",
        "policy": {"type": "seasonal", "active_months": [5, 6, 7, 8, 9]},
    })
    policy = get_device_policy(
        device(), (override,), now=datetime(2026, 1, 15, tzinfo=UTC)
    )
    assert policy.expected_offline is True
    assert policy.in_active_season is False


def test_seasonal_policy_is_not_suppressed_in_active_month():
    override = override_from_mapping({
        "device_id": "dev-1",
        "policy": {"type": "seasonal", "active_months": [5, 6, 7, 8, 9]},
    })
    policy = get_device_policy(
        device(), (override,), now=datetime(2026, 7, 15, tzinfo=UTC)
    )
    assert policy.expected_offline is False
    assert policy.in_active_season is True


def test_legacy_flat_format_remains_supported():
    override = override_from_mapping({
        "device_id": "dev-1",
        "expected_offline": True,
        "ignore_stale": True,
        "profile": "power_controlled",
    })
    policy = get_device_policy(device(), (override,))
    assert policy.expected_offline is True
    assert policy.ignore_stale is True
    assert policy.policy_type == "power_controlled"
