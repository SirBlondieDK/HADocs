from datetime import UTC, datetime, timedelta
from src.hadocs.core.device_overrides import DeviceOverride, match_override

class Entity:
    def __init__(self,eid):
        self.entity_id=eid

class Device:
    def __init__(self,id,name,entities):
        self.device_id=id
        self.name=name
        self.entities=entities

def test_match_device_id():
    d=Device("abc","Lamp",[Entity("light.lamp")])
    ov=DeviceOverride(expected_offline=True,device_id="abc",reason="PIR")
    assert match_override(d,[ov]) is ov

def test_match_name():
    d=Device("abc","Terrasse",[Entity("light.t")])
    ov=DeviceOverride(device_name="Terrasse")
    assert match_override(d,[ov]) is ov

def test_match_entity_glob():
    d=Device("a","b",[Entity("light.wled_terrasse")])
    ov=DeviceOverride(entity_globs=("light.wled_*",))
    assert match_override(d,[ov]) is ov

def test_expired_override_ignored():
    d=Device("abc","Lamp",[Entity("light.lamp")])
    ov=DeviceOverride(device_id="abc", expires_at=datetime.now(UTC) - timedelta(days=1))
    assert match_override(d,[ov]) is None

def test_no_match():
    d=Device("x","Y",[Entity("sensor.temp")])
    assert match_override(d,[]) is None
