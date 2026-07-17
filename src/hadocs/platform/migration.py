from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .paths import AppPaths


@dataclass(frozen=True, slots=True)
class MigrationResult:
    migrated: bool
    messages: list[str]


class MigrationManager:
    """Handles one-time filesystem migrations."""

    def __init__(self, paths: AppPaths | None = None):
        self.paths = paths or AppPaths.discover()

    def migrate(self) -> MigrationResult:
        messages: list[str] = []
        migrated = False

        self.paths.ensure_runtime_directories()

        migrated |= self._move_if_needed(
            self.paths.legacy_config_file,
            self.paths.config_file,
            messages,
        )

        migrated |= self._move_if_needed(
            self.paths.legacy_overrides_file,
            self.paths.overrides_file,
            messages,
        )

        return MigrationResult(
            migrated=migrated,
            messages=messages,
        )

    def _move_if_needed(
        self,
        source: Path,
        destination: Path,
        messages: list[str],
    ) -> bool:
        if not source.exists():
            return False

        if destination.exists():
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)

        messages.append(f"Migrated {source.name}")

        return True