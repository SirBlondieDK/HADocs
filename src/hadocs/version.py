from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductVersion:
    name: str
    version: str
    channel: str

    @property
    def display_version(self) -> str:
        if not self.channel:
            return self.version

        return f"{self.version}-{self.channel}"

    @property
    def display_name(self) -> str:
        return f"{self.name} {self.display_version}"


CORE = ProductVersion(
    name="HADocs Core",
    version="0.3.0",
    channel="alpha",
)

WINDOWS = ProductVersion(
    name="HADocs Windows",
    version="0.15.0",
    channel="rc1",
)

DOCKER = ProductVersion(
    name="HADocs Docker",
    version="0.3.0",
    channel="alpha",
)

HOME_ASSISTANT_ADDON = ProductVersion(
    name="HADocs Home Assistant Add-on",
    version="0.3.0",
    channel="alpha",
)

# Backwards-compatible application metadata.
APP_NAME = "HADocs"
APP_DESCRIPTION = "Home Assistant Documentation & Analysis"

# The current Windows application release remains the public desktop version.
__version__ = WINDOWS.display_version
