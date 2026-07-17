from types import SimpleNamespace

from src.hadocs.core.device_overrides import (
    DeviceOverride,
    get_device_policy,
    override_from_mapping,
)
from src.hadocs.core.device_reachability import (
    ReachabilityStatus,
    determine_device_reachability,
)


def device():
    return SimpleNamespace(device_id="saphe-1", name="Saphe", entities=[])


def test_external_ownership_is_parsed():
    override = override_from_mapping({
        "device_id": "saphe-1",
        "ownership": "external",
    })
    assert override.ownership == "external"


def test_invalid_ownership_becomes_unknown():
    override = override_from_mapping({"ownership": "something-else"})
    assert override.ownership == "unknown"


def test_external_policy_matches_device():
    policy = get_device_policy(
        device(),
        (DeviceOverride(device_id="saphe-1", ownership="external"),),
    )
    assert policy.ownership == "external"
    assert policy.matched is True


def test_external_device_has_external_reachability():
    result = determine_device_reachability(
        device(),
        (DeviceOverride(device_id="saphe-1", ownership="external"),),
    )
    assert result.status is ReachabilityStatus.EXTERNAL
    assert result.confidence == 100
