from __future__ import annotations

from hadocs.providers import HomeAssistantProvider


class StatesCollector:
    """Collect Home Assistant states."""

    def collect(self, provider: HomeAssistantProvider) -> list[dict]:
        return provider.get_states()
