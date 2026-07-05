from src.hadocs.advisor.engine import health_status, estimate_repair_minutes
from src.hadocs.advisor.models import ActionPlan


def test_health_status():
    assert health_status(95) == "EXCELLENT"
    assert health_status(85) == "GOOD"
    assert health_status(70) == "NEEDS ATTENTION"
    assert health_status(40) == "CRITICAL"


def test_estimated_repair_minutes():
    actions = [
        ActionPlan("Fix one", 5, "Reason", 8, estimated_repair_minutes=8),
        ActionPlan("Check one", 4, "Reason", 3, estimated_repair_minutes=5),
        ActionPlan("Cleanup", 3, "Reason", 1, estimated_repair_minutes=3),
    ]

    assert estimate_repair_minutes(actions) == 16
