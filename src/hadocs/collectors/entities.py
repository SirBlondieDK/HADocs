from __future__ import annotations

from src.hadocs.providers import HomeAssistantProvider


class EntitiesCollector:
    """Collect Home Assistant entity registry entries."""

    def collect(self, provider: HomeAssistantProvider) -> list[dict]:
        return provider.get_entities()
