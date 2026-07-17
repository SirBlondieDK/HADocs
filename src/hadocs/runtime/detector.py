from __future__ import annotations

import os
import sys
from pathlib import Path

from src.hadocs.runtime.environment import RuntimeEnvironment


_CONTAINER_MARKERS = (
    Path("/.dockerenv"),
    Path("/run/.containerenv"),
)


def is_home_assistant_addon() -> bool:
    """Return True when HADocs runs as a Home Assistant add-on."""
    return bool(os.environ.get("SUPERVISOR_TOKEN"))


def is_container() -> bool:
    """Return True when HADocs appears to run inside a container."""
    if any(marker.exists() for marker in _CONTAINER_MARKERS):
        return True

    try:
        cgroup = Path("/proc/1/cgroup")
        if cgroup.exists():
            content = cgroup.read_text(encoding="utf-8", errors="ignore").lower()
            return any(
                marker in content
                for marker in ("docker", "containerd", "kubepods", "podman", "lxc")
            )
    except OSError:
        pass

    return False


def uses_hadocs_environment() -> bool:
    """Return True when one or more HADocs environment settings are present."""
    return any(
        os.environ.get(name)
        for name in (
            "HADOCS_HA_URL",
            "HADOCS_TOKEN",
            "HADOCS_CONFIG_FILE",
            "HADOCS_OUTPUT_DIR",
            "HADOCS_CACHE_DIR",
            "HADOCS_PROJECT_NAME",
        )
    )


def detect_runtime() -> RuntimeEnvironment:
    """Detect the current HADocs runtime environment."""
    if is_home_assistant_addon():
        return RuntimeEnvironment.HOME_ASSISTANT_ADDON

    if is_container() and uses_hadocs_environment():
        return RuntimeEnvironment.DOCKER

    if sys.platform == "win32":
        return RuntimeEnvironment.WINDOWS

    return RuntimeEnvironment.LINUX
