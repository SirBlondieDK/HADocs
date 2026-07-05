from src.hadocs.core.classifiers import classify_entity, is_ignored_entity_id


def test_buttons_are_ignored():
    assert is_ignored_entity_id("button.homeassistant_restart")


def test_lights_are_not_ignored():
    ignored, physical, importance, reason = classify_entity("light.kitchen", "mqtt")
    assert not ignored
    assert physical


def test_wled_segments_are_ignored():
    ignored, physical, importance, reason = classify_entity("light.wled_segment_1", "wled")
    assert ignored


def test_mobile_app_storage_is_ignored():
    ignored, physical, importance, reason = classify_entity("sensor.iphone_storage", "mobile_app")
    assert ignored


def test_ring_camera_is_important():
    ignored, physical, importance, reason = classify_entity("camera.front_door", "ring")
    assert not ignored
    assert physical
    assert importance == "important"
