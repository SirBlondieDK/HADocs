from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .paths import AppPaths


@dataclass(frozen=True, slots=True)
class MigrationResult:
    migrated: bool
    messages: list[str]


class MigrationManager:
    """Copy validated legacy settings without deleting or overwriting data."""

    def __init__(self, paths: AppPaths | None = None):
        self.paths = paths or AppPaths.discover()

    def migrate(self) -> MigrationResult:
        messages: list[str] = []
        migrated = False

        self.paths.ensure_runtime_directories()

        migrated |= self._copy_first_valid_json(
            self.paths.legacy_config_candidates,
            self.paths.config_file,
            messages,
            "configuration",
        )
        migrated |= self._copy_first_valid_json(
            self.paths.legacy_overrides_candidates,
            self.paths.overrides_file,
            messages,
            "device overrides",
        )

        return MigrationResult(migrated=migrated, messages=messages)

    def _copy_first_valid_json(
        self,
        sources: tuple[Path, ...],
        destination: Path,
        messages: list[str],
        description: str,
    ) -> bool:
        if destination.exists():
            return False

        for source in sources:
            if source == destination or not source.is_file():
                continue
            try:
                value = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict):
                continue
            if self._copy_without_overwrite(source, destination):
                messages.append(f"Migrated legacy {description} from {source}")
                return True
            return False
        return False

    @staticmethod
    def _copy_without_overwrite(source: Path, destination: Path) -> bool:
        """Publish a same-directory temporary copy only if target is absent."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(
            f".{destination.name}.hadocs-migration-{uuid4().hex}.tmp"
        )
        try:
            shutil.copy2(source, temporary)
            try:
                os.link(temporary, destination)
            except FileExistsError:
                return False
            return True
        finally:
            temporary.unlink(missing_ok=True)
