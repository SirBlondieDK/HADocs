from __future__ import annotations

from enum import Enum


class RuntimeEnvironment(str, Enum):
    HOME_ASSISTANT_ADDON = "home_assistant_addon"
    DOCKER = "docker"
    WINDOWS = "windows"
    LINUX = "linux"
