import math
from collections import Counter, defaultdict
from src.hadocs.domain.findings import FindingCategory, FindingSeverity
from src.hadocs.domain.scoring import CategoryScore, HealthScoreResult

class HealthScoreV2:
    VERSION = 2
    CATEGORY_WEIGHTS = {
        FindingCategory.AVAILABILITY: 0.24,
        FindingCategory.MAINTENANCE: 0.16,
        FindingCategory.CONFIGURATION: 0.18,
        FindingCategory.INTEGRATIONS: 0.18,
        FindingCategory.ENTITY_QUALITY: 0.14,
        FindingCategory.DIAGNOSTICS: 0.10,
    }
    SEVERITY_MULTIPLIERS = {
        FindingSeverity.CRITICAL: 1.8,
        FindingSeverity.WARNING: 1.0,
        FindingSeverity.MAINTENANCE: 0.55,
        FindingSeverity.INFORMATIONAL: 0.0,
    }

    def calculate(self, findings):
        effective = [finding for finding in findings if not finding.suppressed]
        grouped = defaultdict(list)
        for finding in effective:
            grouped[finding.category].append(finding)

        categories = {}
        weighted_score = 0.0
        for category, weight in self.CATEGORY_WEIGHTS.items():
            category_findings = grouped.get(category, [])
            deduction = self._deduction(category_findings)
            score = max(0.0, 100.0 - deduction)
            suppressed_count = sum(
                1 for finding in findings
                if finding.category == category and finding.suppressed
            )
            categories[category] = CategoryScore(
                category, round(score, 1), round(deduction, 1),
                len(category_findings), suppressed_count,
            )
            weighted_score += score * weight

        score = round(max(0.0, min(100.0, weighted_score)), 1)
        penalties = Counter()
        affected = Counter()
        for finding in effective:
            penalties[finding.code] += finding.effective_penalty()
            affected[finding.code] += 1
        top_causes = [
            {'code': code, 'deduction': round(value, 1), 'affected': affected[code]}
            for code, value in penalties.most_common(5)
        ]
        return HealthScoreResult(
            2, score, 100.0, self._grade(score), categories, top_causes,
            len({policy_id for finding in findings for policy_id in finding.applied_policy_ids}),
            sum(1 for finding in findings if finding.suppressed),
        )

    def _deduction(self, findings) -> float:
        by_code = defaultdict(list)
        for finding in findings:
            by_code[finding.code].append(finding)
        total = 0.0
        for group in by_code.values():
            ordered = sorted(group, key=lambda item: item.effective_penalty(), reverse=True)
            for index, finding in enumerate(ordered):
                total += (
                    finding.effective_penalty()
                    * self.SEVERITY_MULTIPLIERS[finding.severity]
                    / math.sqrt(index + 1)
                )
        return min(100.0, total)

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return 'healthy'
        if score >= 75:
            return 'attention'
        if score >= 50:
            return 'degraded'
        return 'critical'
