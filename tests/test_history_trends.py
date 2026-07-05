from src.hadocs.core.history import build_trend_summary, compare_snapshots, sparkline


def test_sparkline_returns_text():
    assert sparkline([60, 70, 80])


def test_trend_summary_empty():
    summary = build_trend_summary([])
    assert summary["scan_count"] == 0
    assert summary["latest"] is None


def test_trend_summary_values():
    history = [
        {"timestamp": "1", "health_score": 60, "problem_entities": 20},
        {"timestamp": "2", "health_score": 75, "problem_entities": 10},
    ]
    summary = build_trend_summary(history)
    assert summary["scan_count"] == 2
    assert summary["best_health"] == 75
    assert summary["worst_health"] == 60
    assert summary["health_change_total"] == 15


def test_compare_snapshots_root_causes():
    previous = {
        "health_score": 60,
        "potential_score": 80,
        "problem_entities": 20,
        "critical_actions": 2,
        "warning_actions": 3,
        "maintenance_actions": 4,
        "root_causes": [{"key": "mqtt"}, {"key": "wled"}],
    }
    current = {
        "health_score": 70,
        "potential_score": 85,
        "problem_entities": 12,
        "critical_actions": 1,
        "warning_actions": 4,
        "maintenance_actions": 2,
        "root_causes": [{"key": "mqtt"}, {"key": "mobile_app"}],
    }
    diff = compare_snapshots(previous, current)
    assert diff["health_delta"] == 10
    assert diff["problem_entity_delta"] == -8
    assert diff["new_root_causes"] == ["mobile_app"]
    assert diff["resolved_root_causes"] == ["wled"]
