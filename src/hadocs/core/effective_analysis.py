from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.hadocs.advisor.engine import build_executive_summary_from_incidents
from src.hadocs.advisor.models import ExecutiveSummary
from src.hadocs.core.device_overrides import DeviceOverride
from src.hadocs.core.effective_incidents import filter_effective_incidents
from src.hadocs.core.incidents import CollapsedIncident, Incident, collapse_incidents
from src.hadocs.core.models import HADocsModel


@dataclass(frozen=True, slots=True)
class EffectiveAnalysis:
    """Single authoritative result of the HADocs analysis pipeline.

    Every consumer (score forecast, executive summary, recommendations,
    root-cause reports, history and exports) must use this object rather than
    rebuilding or filtering incidents independently.
    """

    raw_incidents: tuple[Incident, ...]
    effective_incidents: tuple[Incident, ...]
    root_causes: tuple[CollapsedIncident, ...]
    executive: ExecutiveSummary
    suppressed_incident_count: int

    @property
    def recommendations(self):
        return tuple(self.executive.actions)

    @property
    def potential_gain(self) -> int:
        return max(0, self.executive.potential_score - self.executive.score)

    @property
    def top_recommendation_gain(self) -> int:
        """Return the score gain that is actually achievable from the top fix."""
        if not self.executive.actions:
            return 0
        claimed = max(0, int(self.executive.actions[0].estimated_score_gain))
        return min(claimed, self.potential_gain)


def build_effective_analysis(
    model: HADocsModel,
    raw_incidents: Iterable[Incident],
    overrides: Iterable[DeviceOverride],
    health_score: int,
) -> EffectiveAnalysis:
    """Build the one canonical analysis result used by all report consumers."""

    raw = tuple(raw_incidents)
    effective = tuple(filter_effective_incidents(model, raw, overrides))
    root_causes = tuple(collapse_incidents(list(effective)))
    executive = build_executive_summary_from_incidents(health_score, list(root_causes))

    return EffectiveAnalysis(
        raw_incidents=raw,
        effective_incidents=effective,
        root_causes=root_causes,
        executive=executive,
        suppressed_incident_count=max(0, len(raw) - len(effective)),
    )
