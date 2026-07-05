from src.hadocs.core.incidents import _repair_minutes, _score_gain_from_count, _severity_from_count


def test_severity_from_count():
    assert _severity_from_count(35) == "critical"
    assert _severity_from_count(12) == "warning"
    assert _severity_from_count(2) == "maintenance"


def test_score_gain_from_count():
    assert _score_gain_from_count(60) == 10
    assert _score_gain_from_count(20) == 5
    assert _score_gain_from_count(1) == 1


def test_mobile_repair_time_short():
    assert _repair_minutes("mobile_app_device", 60) == 2
