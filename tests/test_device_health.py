from src.hadocs.core.health import calculate_health_score


class Model:
    devices = {}
    entities = {}


def test_empty_model_health_is_perfect():
    score, notes = calculate_health_score(Model(), [])
    assert score == 100
