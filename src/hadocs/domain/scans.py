from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

class ScanStatus(StrEnum):
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

@dataclass(slots=True)
class ScanRun:
    status: ScanStatus
    id: str = field(default_factory=lambda: uuid4().hex)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    hadocs_version: str | None = None
    home_assistant_version: str | None = None
    raw_finding_count: int = 0
    effective_finding_count: int = 0
    health_score: float | None = None
    error: str | None = None
