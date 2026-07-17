from datetime import UTC, datetime
from src.hadocs.core.device_overrides import DeviceOverride
from src.hadocs.core.device_reachability import ReachabilityStatus, determine_device_reachability
from src.hadocs.core.health import calculate_device_health
from src.hadocs.core.incidents_v2 import build_incidents_v2
from src.hadocs.core.integration_health import calculate_integration_health
from src.hadocs.core.models import DeviceModel, EntityModel, InstallationModel, IntegrationModel

def model_and_device():
    e=EntityModel(entity_id="binary_sensor.wled_online",name="WLED online",domain="binary_sensor",
        platform="wled",state="off",area_id=None,device_id="d1",is_ignored=False,is_physical=True,
        importance="important",attributes={"device_class":"connectivity"},
        last_reported="2026-07-16T17:59:00+00:00")
    d=DeviceModel(device_id="d1",name="WLED Terrasse",area_id=None,manufacturer="WLED",model="ESP32",
        sw_version="",hw_version="",classification="physical",entities=[e])
    i=IntegrationModel(platform="wled",entities=[e],devices=[d])
    m=InstallationModel(areas={},devices={"d1":d},entities={e.entity_id:e},integrations={"wled":i},
        config={},states=[],services=[],labels=[],raw={})
    return m,d

def override():
    return DeviceOverride(device_id="d1",expected_offline=True,reason="Power disconnected intentionally")

def test_reachability_expected_offline():
    _,d=model_and_device()
    assert determine_device_reachability(d,(override(),)).status is ReachabilityStatus.EXPECTED_OFFLINE

def test_health_no_penalty():
    m,_=model_and_device()
    h=calculate_device_health(m,(override(),))[0]
    assert h.score==100 and h.status=="healthy"

def test_incident_is_maintenance():
    m,_=model_and_device()
    incident=next(x for x in build_incidents_v2(m,(override(),)) if x.category=="physical_device")
    assert incident.severity=="maintenance"

def test_integration_no_penalty():
    m,_=model_and_device()
    r=calculate_integration_health(m,now=datetime(2026,7,16,18,tzinfo=UTC),overrides=(override(),))[0]
    assert r.score==100
    assert r.expected_offline_devices==1
    assert r.offline_devices==0
