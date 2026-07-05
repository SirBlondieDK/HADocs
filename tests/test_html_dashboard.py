from src.hadocs.html.dashboard import build_ai_summary


class Executive:
    status = "NEEDS ATTENTION"
    score = 67
    potential_score = 85
    estimated_repair_minutes = 37
    main_cause = "Mobile App devices"


class Incident:
    root_cause = "Mobile App devices"
    affected_entities = ["a", "b"]
    affected_devices = ["Phone"]


def test_ai_summary_mentions_main_root_cause():
    summary = build_ai_summary(Executive(), [Incident()])
    assert "Mobile App devices" in summary
    assert "67" in summary
    assert "85" in summary
