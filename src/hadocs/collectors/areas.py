from __future__ import annotations

from src.hadocs.providers import HomeAssistantProvider


class AreasCollector:
    """Collect Home Assistant area registry entries."""

    def collect(self, provider: HomeAssistantProvider) -> list[dict]:
        return provider.get_areas()
