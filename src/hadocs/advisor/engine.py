from collections import Counter, defaultdict

from src.hadocs.advisor.models import ActionPlan, ExecutiveSummary, Insight
from src.hadocs.core.relationships import RelationshipGraph


def health_status(score: int) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "GOOD"
    if score >= 60:
        return "NEEDS ATTENTION"
    return "CRITICAL"


def estimate_repair_minutes(actions: list[ActionPlan]) -> int:
    if not actions:
        return 0

    minutes = 0
    for action in actions:
        if action.priority >= 5:
            minutes += 8
        elif action.priority == 4:
            minutes += 5
        else:
            minutes += 3

    return min(120, minutes)


def build_insights(model, graph: RelationshipGraph, device_health, recommendations, score: int) -> list[Insight]:
    insights: list[Insight] = []

    problem_devices = [item for item in device_health if item.status == "problem"]
    warning_devices = [item for item in device_health if item.status == "warning"]

    if problem_devices:
        worst = sorted(problem_devices, key=lambda item: item.score)[0]
        affected = len([
            entity for entity in worst.device.entities
            if entity.state in ("unknown", "unavailable")
        ])
        insights.append(
            Insight(
                title="Main device issue",
                message=(
                    f"The device '{worst.device.name}' appears to be the most important problem. "
                    f"It has {affected} unknown or unavailable entities."
                ),
                severity="critical",
                estimated_score_gain=8,
                related_items=[worst.device.name],
            )
        )

    integration_problems = []
    for integration in graph.integrations.values():
        if integration.problem_entities:
            integration_problems.append((integration.platform, len(integration.problem_entities)))

    if integration_problems:
        integration, count = sorted(integration_problems, key=lambda item: item[1], reverse=True)[0]
        insights.append(
            Insight(
                title="Main integration issue",
                message=(
                    f"Most relevant integration problems originate from '{integration}' "
                    f"with {count} relevant problem entities."
                ),
                severity="warning" if count < 10 else "critical",
                estimated_score_gain=min(12, max(3, count // 5)),
                related_items=[integration],
            )
        )

    area_missing = [
        device for device in model.devices.values()
        if device.is_physical and (not device.area_id or device.area_id == "_uden_område")
    ]
    if area_missing:
        insights.append(
            Insight(
                title="Area cleanup",
                message=(
                    f"{len(area_missing)} physical devices are not assigned to an area. "
                    "Assigning areas improves documentation, dashboards, and relationship analysis."
                ),
                severity="maintenance",
                estimated_score_gain=min(8, max(1, len(area_missing) // 10)),
                related_items=[device.name for device in area_missing[:10]],
            )
        )

    ignored_bad = [
        entity for entity in model.entities.values()
        if entity.is_ignored and entity.state in ("unknown", "unavailable")
    ]
    if ignored_bad:
        insights.append(
            Insight(
                title="Noise filtered",
                message=(
                    f"HADocs ignored {len(ignored_bad)} diagnostic or system entities that are "
                    "unknown/unavailable, so they do not unfairly reduce your Health Score."
                ),
                severity="info",
                estimated_score_gain=0,
            )
        )

    if not problem_devices and not warning_devices:
        insights.append(
            Insight(
                title="Installation looks healthy",
                message="No major device health issues were detected.",
                severity="positive",
                estimated_score_gain=0,
            )
        )

    return insights


def build_action_plan(model, graph: RelationshipGraph, device_health, recommendations) -> list[ActionPlan]:
    actions: list[ActionPlan] = []

    for item in sorted(device_health, key=lambda health: health.score):
        if item.status == "problem":
            actions.append(
                ActionPlan(
                    title=f"Fix {item.device.name}",
                    priority=5,
                    reason="; ".join(item.reasons) or "Device has serious health issues.",
                    estimated_score_gain=8,
                    related_items=[entity.entity_id for entity in item.device.entities[:10]],
                )
            )
        elif item.status == "warning":
            actions.append(
                ActionPlan(
                    title=f"Check {item.device.name}",
                    priority=4,
                    reason="; ".join(item.reasons) or "Device has warnings.",
                    estimated_score_gain=3,
                    related_items=[entity.entity_id for entity in item.device.entities[:10]],
                )
            )

    missing_area = [
        device for device in model.devices.values()
        if device.is_physical and (not device.area_id or device.area_id == "_uden_område")
    ]
    if missing_area:
        actions.append(
            ActionPlan(
                title=f"Assign areas to {len(missing_area)} physical devices",
                priority=3,
                reason="Area assignments improve reports, dashboards, and future automation analysis.",
                estimated_score_gain=min(8, max(1, len(missing_area) // 10)),
                related_items=[device.name for device in missing_area[:10]],
            )
        )

    # Deduplicate by title.
    unique = {}
    for action in actions:
        unique.setdefault(action.title, action)

    return sorted(unique.values(), key=lambda action: (-action.priority, -action.estimated_score_gain))


def build_executive_summary(model, graph, device_health, recommendations, score: int) -> ExecutiveSummary:
    actions = build_action_plan(model, graph, device_health, recommendations)
    insights = build_insights(model, graph, device_health, recommendations, score)

    critical_count = sum(1 for action in actions if action.priority >= 5)
    warning_count = sum(1 for action in actions if action.priority == 4)
    maintenance_count = sum(1 for action in actions if action.priority <= 3)

    potential_gain = min(30, sum(action.estimated_score_gain for action in actions[:8]))
    potential_score = min(100, score + potential_gain)

    main_cause = "No major issue detected"
    critical_insights = [insight for insight in insights if insight.severity in {"critical", "warning"}]
    if critical_insights:
        main_cause = critical_insights[0].title

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
