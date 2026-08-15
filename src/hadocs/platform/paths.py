from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


INSTALLER_MARKER = ".hadocs-installed"
RUNTIME_ROOT_ENVIRONMENT = "HADOCS_ROOT"


class RuntimePathError(RuntimeError):
    """Raised when a safe runtime/data root cannot be determined."""


class RuntimeMode(str, Enum):
    EXPLICIT = "explicit"
    WINDOWS_INSTALLED = "windows_installed"
    WINDOWS_PORTABLE = "windows_portable"
    SOURCE = "source"
    HOME_ASSISTANT_ADDON = "home_assistant_addon"
    CONTAINER = "container"


def _resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def windows_local_app_data() -> Path:
    """Return the Windows per-user Known Folder exposed by LOCALAPPDATA."""

    value = os.environ.get("LOCALAPPDATA", "").strip()
    if not value:
        raise RuntimePathError(
            "HADocs cannot determine a writable Windows data directory because "
            "LOCALAPPDATA is unavailable."
        )
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise RuntimePathError(
            "HADocs cannot use LOCALAPPDATA because it is not an absolute path."
        )
    return candidate.resolve()


def _resolve_within(root: Path, candidate: Path, *, description: str) -> Path:
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise RuntimePathError(
            f"Relative {description} must stay inside its configured root."
        ) from error
    return resolved


def _is_frozen_windows() -> bool:
    return sys.platform == "win32" and bool(getattr(sys, "frozen", False))


def _application_root(cwd: Path) -> Path:
    if _is_frozen_windows():
        return _resolved(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return cwd


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Separate immutable application resources from mutable runtime data.

    Discovery precedence is: explicit ``root_dir`` argument, documented
    ``HADOCS_ROOT`` override, installed frozen Windows marker, portable frozen
    Windows, source checkout, Home Assistant App, then container/runtime
    fallback. Home Assistant and container deployments retain their explicit
    environment paths for config/output/cache.
    """

    application_root: Path
    data_root: Path
    mode: RuntimeMode
    executable_root: Path

    @classmethod
    def discover(cls, root_dir: str | Path | None = None) -> "AppPaths":
        cwd = Path.cwd().resolve()
        app_root = _application_root(cwd)
        executable_root = (
            Path(sys.executable).resolve().parent if _is_frozen_windows() else cwd
        )

        explicit = root_dir
        if explicit is None:
            explicit = os.environ.get(RUNTIME_ROOT_ENVIRONMENT) or None
        if explicit is not None:
            return cls(
                application_root=app_root,
                data_root=_resolved(explicit),
                mode=RuntimeMode.EXPLICIT,
                executable_root=executable_root,
            )

        if _is_frozen_windows():
            if (executable_root / INSTALLER_MARKER).is_file():
                data_root = windows_local_app_data() / "HADocs"
                mode = RuntimeMode.WINDOWS_INSTALLED
            else:
                data_root = executable_root
                mode = RuntimeMode.WINDOWS_PORTABLE
            return cls(app_root, data_root, mode, executable_root)

        # A repository invocation intentionally keeps its historical CWD root,
        # even when the checkout itself is mounted in a development container.
        if (cwd / "main.py").is_file() and (cwd / "pyproject.toml").is_file():
            return cls(app_root, cwd, RuntimeMode.SOURCE, cwd)

        if os.environ.get("SUPERVISOR_TOKEN"):
            return cls(
                app_root,
                cwd,
                RuntimeMode.HOME_ASSISTANT_ADDON,
                cwd,
            )

        return cls(app_root, cwd, RuntimeMode.CONTAINER, cwd)

    @property
    def root_dir(self) -> Path:
        """Backward-compatible name for the mutable data root."""

        return self.data_root

    @property
    def config_dir(self) -> Path:
        return self.data_root / "config"

    @property
    def output_dir(self) -> Path:
        return self.data_root / "output"

    @property
    def cache_dir(self) -> Path:
        return self.data_root / "cache"

    @property
    def logs_dir(self) -> Path:
        return self.data_root / "logs"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.json"

    @property
    def overrides_file(self) -> Path:
        return self.config_dir / "device_overrides.json"

    @property
    def legacy_config_file(self) -> Path:
        return self.data_root / "config.json"

    @property
    def legacy_overrides_file(self) -> Path:
        return self.data_root / "device_overrides.json"

    @property
    def legacy_config_candidates(self) -> tuple[Path, ...]:
        if self.mode is RuntimeMode.WINDOWS_INSTALLED:
            return (
                self.executable_root / "config" / "config.json",
                self.executable_root / "config.json",
            )
        return (self.legacy_config_file,)

    @property
    def legacy_overrides_candidates(self) -> tuple[Path, ...]:
        if self.mode is RuntimeMode.WINDOWS_INSTALLED:
            return (
                self.executable_root / "config" / "device_overrides.json",
                self.executable_root / "device_overrides.json",
            )
        return (self.legacy_overrides_file,)

    def resolve_data_path(self, value: str | Path) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return _resolve_within(
            self.data_root,
            candidate,
            description="runtime path",
        )

    def resolve_resource_path(self, value: str | Path) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return _resolve_within(
            self.application_root,
            candidate,
            description="resource path",
        )

    def ensure_runtime_directories(self) -> None:
        for directory in (
            self.config_dir,
            self.output_dir,
            self.cache_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
