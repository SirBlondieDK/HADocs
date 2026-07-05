from dataclasses import dataclass, field


@dataclass
class Insight:
    title: str
    message: str
    severity: str = "info"
    estimated_score_gain: int = 0
    related_items: list[str] = field(default_factory=list)


@dataclass
class ActionPlan:
    title: str
    priority: int
    reason: str
    estimated_score_gain: int
    related_items: list[str] = field(default_factory=list)
    estimated_repair_minutes: int = 0


@dataclass
class ExecutiveSummary:
    status: str
    score: int
    potential_score: int
    critical_count: int
    warning_count: int
    maintenance_count: int
    estimated_repair_minutes: int
    main_cause: str
    insights: list[Insight]
    actions: list[ActionPlan]
