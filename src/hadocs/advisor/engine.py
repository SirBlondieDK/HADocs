from src.hadocs.advisor.models import ActionPlan, ExecutiveSummary, Insight
from src.hadocs.core.incidents import Incident


def health_status(score: int) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "GOOD"
    if score >= 60:
        return "NEEDS ATTENTION"
    return "CRITICAL"


def estimate_repair_minutes(actions: list[ActionPlan]) -> int:
    return min(120, sum(action.estimated_repair_minutes for action in actions))


def priority_from_severity(severity: str) -> int:
    return {
        "critical": 5,
        "warning": 4,
        "maintenance": 3,
        "info": 1,
    }.get(severity, 1)


def build_insights_from_incidents(incidents: list[Incident]) -> list[Insight]:
    insights: list[Insight] = []

    if not incidents:
        return [
            Insight(
                title="Installation looks healthy",
                message="No major root causes were detected.",
                severity="positive",
            )
        ]

    main = incidents[0]
    insights.append(
        Insight(
            title="Main root cause",
            message=(
                f"{main.root_cause} is the strongest detected root cause. "
                f"It affects {len(main.affected_entities)} relevant entities."
            ),
            severity=main.severity,
            estimated_score_gain=main.estimated_score_gain,
            related_items=[main.root_cause],
        )
    )

    total_symptoms = sum(len(incident.affected_entities) for incident in incidents)
    top_three_symptoms = sum(len(incident.affected_entities) for incident in incidents[:3])
    if total_symptoms and top_three_symptoms:
        percent = round((top_three_symptoms / total_symptoms) * 100)
        insights.append(
            Insight(
                title="Few causes create most symptoms",
                message=(
                    f"The top {min(3, len(incidents))} incidents explain about {percent}% "
                    "of relevant unknown/unavailable symptoms."
                ),
                severity="info",
                estimated_score_gain=sum(i.estimated_score_gain for i in incidents[:3]),
                related_items=[i.root_cause for i in incidents[:3]],
            )
        )

    mobile_incidents = [incident for incident in incidents if incident.category == "mobile_app_device"]
    if mobile_incidents:
        affected = sum(len(incident.affected_entities) for incident in mobile_incidents)
        insights.append(
            Insight(
                title="Mobile App root cause",
                message=(
                    f"{len(mobile_incidents)} Mobile App devices account for "
                    f"{affected} relevant unavailable/unknown entities."
                ),
                severity="warning",
                estimated_score_gain=min(12, sum(i.estimated_score_gain for i in mobile_incidents)),
                related_items=[i.root_cause for i in mobile_incidents],
            )
        )

    return insights


def build_action_plan_from_incidents(incidents: list[Incident]) -> list[ActionPlan]:
    actions = []
    for incident in incidents:
        actions.append(
            ActionPlan(
                title=incident.title,
                priority=priority_from_severity(incident.severity),
                reason=incident.recommendation,
                estimated_score_gain=incident.estimated_score_gain,
                related_items=incident.affected_entities[:12] or incident.affected_devices[:12],
                estimated_repair_minutes=incident.estimated_repair_minutes,
            )
        )

    return sorted(actions, key=lambda action: (-action.priority, -action.estimated_score_gain))


def build_executive_summary_from_incidents(score: int, incidents: list[Incident]) -> ExecutiveSummary:
    actions = build_action_plan_from_incidents(incidents)
    insights = build_insights_from_incidents(incidents)

    critical_count = sum(1 for incident in incidents if incident.severity == "critical")
    warning_count = sum(1 for incident in incidents if incident.severity == "warning")
    maintenance_count = sum(1 for incident in incidents if incident.severity == "maintenance")

    potential_gain = min(24, sum(action.estimated_score_gain for action in actions[:5]))
    potential_score = min(100, score + potential_gain)

    main_cause = incidents[0].root_cause if incidents else "No major issue detected"

    return ExecutiveSummary(
        status=health_status(score),
        score=score,
        potential_score=potential_score,
        critical_count=critical_count,
        warning_count=warning_count,
        maintenance_count=maintenance_count,
        estimated_repair_minutes=estimate_repair_minutes(actions[:8]),
        main_cause=main_cause,
        insights=insights,
        actions=actions,
    )


# Backwards-compatible function name.
def build_executive_summary(model, graph, device_health, recommendations, score: int) -> ExecutiveSummary:
    from src.hadocs.core.incidents import build_incidents
    incidents = build_incidents(model, graph)
    return build_executive_summary_from_incidents(score, incidents)
