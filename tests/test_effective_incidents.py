from types import SimpleNamespace
from src.hadocs.core.effective_incidents import filter_effective_incidents
from src.hadocs.core.incidents import Incident


def entity(eid, did, disabled_by=None):
    return SimpleNamespace(entity_id=eid, device_id=did, disabled_by=disabled_by, disabled=False, state="unavailable", registry={})


def device(did, name):
    return SimpleNamespace(device_id=did, name=name, entities=[])


def override(did):
    return SimpleNamespace(device_id=did, device_name=None, entity_globs=(), expected_offline=True, ownership="owned", purpose="temporary", policy_type="power_controlled", ignore_battery=False, ignore_stale=False, active_months=(), reason="", expires_at=None, expired=lambda now=None: False)


def test_expected_offline_device_incident_is_removed():
    e = entity("switch.pool", "pool-id")
    model = SimpleNamespace(entities={e.entity_id: e}, devices={"pool-id": device("pool-id", "Pool")})
    incident = Incident("device:pool-id", "Pool has 1 relevant unavailable/unknown entities", "physical_device", "maintenance", "Pool", [e.entity_id], ["Pool"], [], "", 1, 3)
    assert filter_effective_incidents(model, [incident], [override("pool-id")]) == []


def test_disabled_entity_incident_is_removed():
    e = entity("light.disabled", "light-id", "user")
    model = SimpleNamespace(entities={e.entity_id: e}, devices={"light-id": device("light-id", "Disabled light")})
    incident = Incident("device:light-id", "Disabled light issue", "physical_device", "maintenance", "Disabled light", [e.entity_id], ["Disabled light"])
    assert filter_effective_incidents(model, [incident]) == []
