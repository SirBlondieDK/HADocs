from pathlib import Path

from src.hadocs.core.device_overrides import (
    DeviceOverride,
    load_device_overrides_file,
    remove_device_override,
    save_device_overrides_file,
    upsert_device_override,
)


def test_save_upsert_and_remove_device_override(tmp_path: Path):
    path = tmp_path / "config" / "device_overrides.json"
    first = DeviceOverride(
        device_id="device-1",
        device_name="Garden lights",
        ownership="owned",
        purpose="seasonal",
        policy_type="seasonal",
        ignore_stale=True,
        active_months=(1, 11, 12),
        reason="Christmas lights",
    )

    save_device_overrides_file(path, [first])
    loaded = load_device_overrides_file(path)
    assert loaded == (first,)

    updated = DeviceOverride(
        device_id="device-1",
        device_name="Garden lights",
        ownership="owned",
        purpose="seasonal",
        policy_type="seasonal",
        expected_offline=True,
        active_months=(11, 12),
    )
    result = upsert_device_override(path, updated)
    assert result == (updated,)
    assert path.with_name(path.name + ".bak").exists()

    result = remove_device_override(path, "device-1")
    assert result == ()
    assert load_device_overrides_file(path) == ()


def test_save_rejects_override_without_target(tmp_path: Path):
    path = tmp_path / "device_overrides.json"
    try:
        save_device_overrides_file(path, [DeviceOverride()])
    except ValueError as exc:
        assert "must target" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
