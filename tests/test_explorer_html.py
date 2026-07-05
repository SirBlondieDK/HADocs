from src.hadocs.html.explorer import render_index


def test_render_index_contains_counts():
    html = render_index({
        "counts": {"devices": 2, "entities": 3, "integrations": 1, "areas": 4}
    })
    assert "Explorer" in html
    assert "Devices" in html
    assert "Entities" in html
