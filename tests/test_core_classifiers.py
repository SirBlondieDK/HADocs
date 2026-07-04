from src.hadocs.core.classifiers import classify_device


def test_integration_device_is_system():
    device = {"manufacturer": "Somebody", "model": "integration", "name": "Some integration"}
    assert classify_device(device, {"sensor"}, {"hacs"}) == "system"


def test_light_device_is_physical():
    device = {"manufacturer": "Tuya", "model": "Zigbee light", "name": "Kitchen light"}
    assert classify_device(device, {"light", "sensor"}, {"mqtt"}) == "physical"


def test_spotify_device_is_system():
    device = {"manufacturer": "Spotify", "model": "", "name": "Spotify"}
    assert classify_device(device, {"media_player"}, {"spotify"}) == "system"
