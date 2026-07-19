from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from .findings import FindingCategory, FindingSeverity, TargetType

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(slots=True)
class PolicyScope:
    target_type: TargetType | None = None
    target_id: str | None = None
    device_id: str | None = None
    entity_id: str | None = None
    integration_id: str | None = None
    area_id: str | None = None
    finding_codes: set[str] = field(default_factory=set)
    categories: set[FindingCategory] = field(default_factory=set)
    metadata_equals: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class PolicyAction:
    suppress: bool = False
    reclassify_as: FindingSeverity | None = None
    penalty_multiplier: float = 1.0
    add_tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.penalty_multiplier < 0:
            raise ValueError('penalty_multiplier cannot be negative')

@dataclass(slots=True)
class Policy:
    name: str
    scope: PolicyScope
    action: PolicyAction
    reason: str
    id: str = field(default_factory=lambda: uuid4().hex)
    enabled: bool = True
    priority: int = 100
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError('Policy name cannot be empty')
        if not self.reason.strip():
            raise ValueError('Policy reason cannot be empty')

    def is_active(self, now: datetime | None = None) -> bool:
        current = now or utc_now()
        return (
            self.enabled
            and (self.starts_at is None or current >= self.starts_at)
            and (self.expires_at is None or current < self.expires_at)
        )
