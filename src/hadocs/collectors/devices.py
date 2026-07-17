from __future__ import annotations

from src.hadocs.providers import HomeAssistantProvider


class DevicesCollector:
    """Collect Home Assistant device registry entries."""

    def collect(self, provider: HomeAssistantProvider) -> list[dict]:
        return provider.get_devices()
