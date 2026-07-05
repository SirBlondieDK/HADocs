from src.hadocs.explorer.builder import build_search_index


def test_build_search_index():
    data = {
        "areas": [{"id": "kitchen", "name": "Kitchen"}],
        "devices": [{"id": "dev1", "name": "Lamp"}],
        "entities": [{"id": "light.lamp", "name": "Lamp", "domain": "light"}],
        "integrations": [{"id": "mqtt", "name": "mqtt"}],
    }
    index = build_search_index(data)
    assert len(index) == 4
    assert any(item["title"] == "Lamp" for item in index)
