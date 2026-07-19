from dataclasses import dataclass, field
from .findings import FindingCategory

@dataclass(slots=True, frozen=True)
class CategoryScore:
    category: FindingCategory
    score: float
    deduction: float
    finding_count: int
    suppressed_count: int = 0

@dataclass(slots=True, frozen=True)
class HealthScoreResult:
    version: int
    score: float
    potential_score: float
    grade: str
    categories: dict[FindingCategory, CategoryScore]
    top_causes: list[dict[str, object]] = field(default_factory=list)
    applied_policy_count: int = 0
    suppressed_finding_count: int = 0
