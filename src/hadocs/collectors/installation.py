from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from hadocs.collectors.areas import AreasCollector
from hadocs.collectors.config import ConfigCollector
from hadocs.collectors.devices import DevicesCollector
from hadocs.collectors.entities import EntitiesCollector
from hadocs.collectors.labels import LabelsCollector
from hadocs.collectors.native_integration_status import (
    NativeIntegrationStatusCollector,
)
from hadocs.collectors.services import ServicesCollector
from hadocs.collectors.states import StatesCollector
from hadocs.providers import HomeAssistantProvider


LogFunction = Callable[[str], None]


class InstallationCollector:
    """Collect a complete Home Assistant installation snapshot."""

    def __init__(
        self,
        provider: HomeAssistantProvider,
        config: dict,
        log: LogFunction = print,
    ):
        self.provider = provider
        self.config = config
        self.log = log

    def collect(self) -> dict:
        data = {
            "states": self._collect(
                "states",
                StatesCollector().collect,
            ),
            "config": self._collect(
                "config",
                ConfigCollector().collect,
            ),
            "services": self._collect(
                "services",
                ServicesCollector().collect,
            ),
            "entities": self._collect(
                "entities",
                EntitiesCollector().collect,
            ),
            "devices": self._collect(
                "devices",
                DevicesCollector().collect,
            ),
            "areas": self._collect(
                "areas",
                AreasCollector().collect,
            ),
        }

        self.log("Collecting labels...")
        data["labels"] = LabelsCollector().collect(
            self.provider,
            self.log,
        )

        native_status_enabled = self.config.get(
            "hask_native_integration_status_enabled", False
        )
        if not isinstance(native_status_enabled, bool):
            raise ValueError(
                "hask_native_integration_status_enabled must be a boolean value"
            )
        if native_status_enabled:
            from hadocs.hask_database import HaskDatabaseApplicationConfig

            database = HaskDatabaseApplicationConfig.from_application_config(
                self.config
            )
            if database.database.enabled and database.identity is not None:
                self.log("Collecting native integration status...")
                data["native_integration_status"] = (
                    NativeIntegrationStatusCollector().collect(self.provider)
                )

        self._write_raw_cache(data)

        return data

    def _collect(self, name: str, collector) -> object:
        self.log(f"Collecting {name}...")
        return collector(self.provider)

    def _write_raw_cache(self, data: dict) -> None:
        if not bool(self.config.get("save_raw_cache", False)):
            return

        cache = Path(self.config.get("cache_dir", "cache"))
        cache.mkdir(parents=True, exist_ok=True)

        self.log(
            "WARNING: Raw Home Assistant API responses will be written to disk. "
            "These files may contain sensitive information."
        )

        for name, value in data.items():
            (cache / f"{name}.json").write_text(
                json.dumps(value, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
