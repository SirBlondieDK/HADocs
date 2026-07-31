from __future__ import annotations

from dataclasses import dataclass


# One product-version authority for source, wheel, CLI, GUI, frozen builds,
# and HASK compatibility negotiation. The release number was already the
# documented public desktop runtime baseline; the preview channel is kept
# separately so SemVer minimum checks use the stable release triplet.
RELEASE_VERSION = "0.17.0"
RELEASE_CHANNEL = "rc1"


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
    version=RELEASE_VERSION,
    channel=RELEASE_CHANNEL,
)

WINDOWS = ProductVersion(
    name="HADocs Windows",
    version=RELEASE_VERSION,
    channel=RELEASE_CHANNEL,
)

DOCKER = ProductVersion(
    name="HADocs Docker",
    version=RELEASE_VERSION,
    channel=RELEASE_CHANNEL,
)

HOME_ASSISTANT_ADDON = ProductVersion(
    name="HADocs Home Assistant Add-on",
    version=RELEASE_VERSION,
    channel=RELEASE_CHANNEL,
)

# Backwards-compatible application metadata.
APP_NAME = "HADocs"
APP_DESCRIPTION = "Home Assistant Documentation & Analysis"

# The current Windows application release remains the public desktop version.
__version__ = WINDOWS.display_version
