from src.hadocs.advisor.models import ActionPlan, ExecutiveSummary, Insight
from src.hadocs.core.incidents import CollapsedIncident, Incident, collapse_incidents


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


def build_insights_from_incidents(incidents: list[CollapsedIncident]) -> list[Insight]:
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
                f"It affects {len(main.affected_entities)} relevant entities "
                f"across {len(main.affected_devices)} devices."
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
                    f"The top {min(3, len(incidents))} root causes explain about {percent}% "
                    "of relevant unknown/unavailable symptoms."
                ),
                severity="info",
                estimated_score_gain=min(16, sum(i.estimated_score_gain for i in incidents[:3])),
                related_items=[i.root_cause for i in incidents[:3]],
            )
        )

    mobile_incidents = [incident for incident in incidents if incident.category == "mobile_app_group"]
    if mobile_incidents:
        incident = mobile_incidents[0]
        insights.append(
            Insight(
                title="Mobile App root cause",
                message=(
                    f"{len(incident.affected_devices)} Mobile App devices account for "
                    f"{len(incident.affected_entities)} relevant unavailable/unknown entities."
                ),
                severity="warning",
                estimated_score_gain=incident.estimated_score_gain,
                related_items=incident.affected_devices,
            )
        )

    hidden_children = sum(len(incident.child_incidents) for incident in incidents)
    if hidden_children:
        insights.append(
            Insight(
                title="Noise collapsed",
                message=(
                    f"HADocs collapsed {hidden_children} child incidents into parent root causes "
                    "to make the report easier to act on."
                ),
                severity="info",
            )
        )

    return insights


def build_action_plan_from_incidents(incidents: list[CollapsedIncident]) -> list[ActionPlan]:
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


def build_executive_summary_from_incidents(score: int, incidents: list[Incident | CollapsedIncident]) -> ExecutiveSummary:
    if incidents and isinstance(incidents[0], Incident):
        incidents = collapse_incidents(incidents)  # type: ignore[assignment]

    actions = build_action_plan_from_incidents(incidents)  # type: ignore[arg-type]
    insights = build_insights_from_incidents(incidents)  # type: ignore[arg-type]

    critical_count = sum(1 for incident in incidents if incident.severity == "critical")
    warning_count = sum(1 for incident in incidents if incident.severity == "warning")
    maintenance_count = sum(1 for incident in incidents if incident.severity == "maintenance")

    # Conservative: only count the top 3 most impactful fixes.
    potential_gain = min(18, sum(action.estimated_score_gain for action in actions[:3]))
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


def build_executive_summary(model, graph, device_health, recommendations, score: int) -> ExecutiveSummary:
    from src.hadocs.core.incidents import build_incidents
    incidents = collapse_incidents(build_incidents(model, graph))
    return build_executive_summary_from_incidents(score, incidents)
