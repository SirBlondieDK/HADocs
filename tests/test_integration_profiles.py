from src.hadocs.intelligence.integration_profiles import get_integration_profile

def test_zigbee_profile():
    p=get_integration_profile("zigbee2mqtt")
    assert p.supports_sleeping_devices
    assert p.has_bridge

def test_mobile_profile():
    assert get_integration_profile("mobile_app").behavior.value=="hybrid"

def test_unknown_profile():
    assert get_integration_profile("my_custom").platform=="my_custom"
