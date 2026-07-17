from __future__ import annotations

from src.hadocs.providers import HomeAssistantProvider


class ConfigCollector:
    """Collect Home Assistant configuration."""

    def collect(self, provider: HomeAssistantProvider) -> dict:
        return provider.get_config()
