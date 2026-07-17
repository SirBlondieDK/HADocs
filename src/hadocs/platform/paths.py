from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    """
    Central path resolver for HADocs.

    All runtime paths should eventually be accessed through this class
    instead of being constructed directly throughout the codebase.
    """

    root_dir: Path

    @classmethod
    def discover(cls, root_dir: str | Path | None = None) -> "AppPaths":
        if root_dir is not None:
            resolved_root = Path(root_dir).expanduser().resolve()
            return cls(root_dir=resolved_root)

        env_root = os.getenv("HADOCS_ROOT")
        if env_root:
            return cls(root_dir=Path(env_root).expanduser().resolve())

        return cls(root_dir=Path.cwd().resolve())

    @property
    def config_dir(self) -> Path:
        return self.root_dir / "config"

    @property
    def output_dir(self) -> Path:
        return self.root_dir / "output"

    @property
    def cache_dir(self) -> Path:
        return self.root_dir / "cache"

    @property
    def logs_dir(self) -> Path:
        return self.root_dir / "logs"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.json"

    @property
    def overrides_file(self) -> Path:
        return self.config_dir / "device_overrides.json"

    @property
    def legacy_config_file(self) -> Path:
        return self.root_dir / "config.json"

    @property
    def legacy_overrides_file(self) -> Path:
        return self.root_dir / "device_overrides.json"

    def ensure_runtime_directories(self) -> None:
        for directory in (
            self.config_dir,
            self.output_dir,
            self.cache_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)