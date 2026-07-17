from datetime import UTC, datetime, timedelta
from src.hadocs.core.device_overrides import (
    DeviceOverride, get_device_policy, load_device_overrides, match_override,
)

class Entity:
    def __init__(self, entity_id): self.entity_id = entity_id
class Device:
    def __init__(self, device_id, name, entities):
        self.device_id, self.name, self.entities = device_id, name, entities

def test_device_id_has_highest_priority():
    d=Device("abc","Terrasse",[Entity("light.wled_terrasse")])
    by_name=DeviceOverride(device_name="Terrasse")
    by_id=DeviceOverride(device_id="abc", expected_offline=True)
    assert match_override(d,[by_name,by_id]) == (by_id,"device_id")

def test_entity_glob_matches():
    d=Device("a","b",[Entity("light.wled_terrasse")])
    o=DeviceOverride(entity_globs=("light.wled_*",))
    assert match_override(d,[o]) == (o,"entity_glob")

def test_expired_override_is_ignored():
    d=Device("abc","Lamp",[Entity("light.lamp")])
    o=DeviceOverride(device_id="abc", expires_at=datetime.now(UTC)-timedelta(days=1))
    assert match_override(d,[o]) is None

def test_policy_values():
    d=Device("abc","Lamp",[Entity("light.lamp")])
    o=DeviceOverride(device_id="abc", expected_offline=True, reason="PIR")
    p=get_device_policy(d,[o])
    assert p.expected_offline and p.reason=="PIR"

def test_load_from_config(tmp_path):
    items = load_device_overrides(
        {"device_overrides": [{"device_id": "abc", "expected_offline": True}]},
        base_dir=tmp_path,
    )
    assert len(items) == 1 and items[0].expected_offline
