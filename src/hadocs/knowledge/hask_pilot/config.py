from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class PilotConfig:
    enabled: bool = False
    bundle_path: Path | None = None
    strict_validation: bool = True

    @classmethod
    def from_environment(cls) -> "PilotConfig":
        raw_path = os.getenv("HADOCS_HASK_BUNDLE_PATH", "").strip()
        return cls(
            enabled=_bool("HADOCS_HASK_PILOT_ENABLED", False),
            bundle_path=Path(raw_path) if raw_path else None,
            strict_validation=_bool("HADOCS_HASK_STRICT_VALIDATION", True),
        )
