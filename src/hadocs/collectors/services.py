from __future__ import annotations

from hadocs.providers import HomeAssistantProvider


class ServicesCollector:
    """Collect Home Assistant services."""

    def collect(self, provider: HomeAssistantProvider) -> list[dict]:
        return provider.get_services()
