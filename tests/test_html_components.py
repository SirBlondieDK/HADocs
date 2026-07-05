from src.hadocs.html.components import esc, health_ring


def test_escape():
    assert esc("<script>") == "&lt;script&gt;"


def test_health_ring_contains_score():
    html = health_ring(67)
    assert "67" in html
    assert "<svg" in html
