from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

class FindingCategory(StrEnum):
    AVAILABILITY = 'availability'
    MAINTENANCE = 'maintenance'
    CONFIGURATION = 'configuration'
    INTEGRATIONS = 'integrations'
    ENTITY_QUALITY = 'entity_quality'
    DIAGNOSTICS = 'diagnostics'

class FindingSeverity(StrEnum):
    CRITICAL = 'critical'
    WARNING = 'warning'
    MAINTENANCE = 'maintenance'
    INFORMATIONAL = 'informational'

class TargetType(StrEnum):
    ENTITY = 'entity'
    DEVICE = 'device'
    INTEGRATION = 'integration'
    AREA = 'area'
    SYSTEM = 'system'

@dataclass(slots=True)
class Finding:
    code: str
    category: FindingCategory
    severity: FindingSeverity
    target_type: TargetType
    target_id: str
    message: str
    penalty: float
    confidence: float = 1.0
    id: str = field(default_factory=lambda: uuid4().hex)
    device_id: str | None = None
    entity_id: str | None = None
    integration_id: str | None = None
    area_id: str | None = None
    duration_seconds: int | None = None
    occurrences: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    suppressed: bool = False
    original_severity: FindingSeverity | None = None
    applied_policy_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError('Finding code cannot be empty')
        if not self.target_id.strip():
            raise ValueError('target_id cannot be empty')
        if self.penalty < 0:
            raise ValueError('penalty cannot be negative')
        if not 0 <= self.confidence <= 1:
            raise ValueError('confidence must be between 0 and 1')

    def effective_penalty(self) -> float:
        if self.suppressed or self.severity == FindingSeverity.INFORMATIONAL:
            return 0.0
        return self.penalty * self.confidence
