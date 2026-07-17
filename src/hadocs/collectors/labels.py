from __future__ import annotations

from collections.abc import Callable

from src.hadocs.providers import HomeAssistantProvider


LogFunction = Callable[[str], None]


class LabelsCollector:
    """Collect Home Assistant labels when the registry is supported."""

    def collect(
        self,
        provider: HomeAssistantProvider,
        log: LogFunction = print,
    ) -> list[dict]:
        try:
            return provider.get_labels()
        except Exception as exc:
            log(f"Labels skipped: {exc}")
            return []
