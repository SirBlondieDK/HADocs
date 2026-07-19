from dataclasses import dataclass
from src.hadocs.intelligence.policy_engine import PolicyEngine
from src.hadocs.intelligence.health_score_v2 import HealthScoreV2

@dataclass(slots=True, frozen=True)
class PolicyPreview:
    current_score: float
    preview_score: float
    score_change: float
    affected_findings: int
    suppressed_findings: int

class PreviewPolicyApplication:
    def __init__(self, engine=None, scorer=None) -> None:
        self.engine = engine or PolicyEngine()
        self.scorer = scorer or HealthScoreV2()

    def run(self, findings, existing_policies, candidate):
        before = self.engine.apply(findings, existing_policies)
        after = self.engine.apply(findings, [*existing_policies, candidate])
        current = self.scorer.calculate(before)
        preview = self.scorer.calculate(after)
        affected = sum(
            1 for old, new in zip(before, after, strict=True)
            if (old.suppressed, old.severity, old.penalty)
            != (new.suppressed, new.severity, new.penalty)
        )
        return PolicyPreview(
            current.score,
            preview.score,
            round(preview.score - current.score, 1),
            affected,
            preview.suppressed_finding_count,
        )
