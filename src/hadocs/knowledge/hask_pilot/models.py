from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LocalEvidence:
    evidence_id: str
    state: str
    details: str = ""


@dataclass(frozen=True, slots=True)
class CanonicalEvidenceMatch:
    local_evidence_id: str
    canonical_ids: tuple[str, ...]
    status: str
    ambiguous: bool = False


@dataclass(frozen=True, slots=True)
class KnowledgeCandidate:
    candidate_id: str
    title: str
    description: str
    supporting_canonical_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    competing_causes: tuple[str, ...]
    applicability: tuple[dict[str, Any], ...]
    default_knowledge_weight: float
    scenarios: tuple[str, ...]
    recommendations: tuple[str, ...]
    verification: tuple[str, ...]
    provenance: tuple[str, ...]
    conflicts: tuple[dict[str, Any], ...]
    known_gaps: tuple[dict[str, Any], ...]
    confirmed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
