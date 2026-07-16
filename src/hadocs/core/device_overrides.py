from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
from typing import Iterable

@dataclass(frozen=True)
class DeviceOverride:
    expected_offline: bool=False
    ignore_battery: bool=False
    ignore_stale: bool=False
    reason: str=""
    expires_at: datetime|None=None
    device_id: str|None=None
    device_name: str|None=None
    entity_globs: tuple[str,...]=()

    def expired(self, now: datetime|None=None)->bool:
        if self.expires_at is None:
            return False
        now = now or datetime.now(UTC)
        return now >= self.expires_at

def match_override(device, overrides: Iterable[DeviceOverride], now: datetime|None=None):
    """Return first active override matching device_id, name or entity glob."""
    for ov in overrides:
        if ov.expired(now):
            continue
        if ov.device_id and getattr(device,"device_id",None)==ov.device_id:
            return ov
        if ov.device_name and getattr(device,"name",None)==ov.device_name:
            return ov
        if ov.entity_globs:
            for ent in getattr(device,"entities",[]):
                eid=getattr(ent,"entity_id","")
                if any(fnmatch(eid,g) for g in ov.entity_globs):
                    return ov
    return None
