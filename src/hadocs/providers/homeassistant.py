from __future__ import annotations

from typing import Any

from src.hadocs.api.client import HomeAssistantAPI


class HomeAssistantProvider:
    """Provide Home Assistant data without exposing API transport details."""

    def __init__(self, api: HomeAssistantAPI):
        self._api = api

    @classmethod
    def from_config(cls, config: dict) -> "HomeAssistantProvider":
        return cls(
            HomeAssistantAPI(
                url=config["ha_url"],
                token=config["token"],
            )
        )

    def test_connection(self) -> Any:
        return self._api.test_connection()

    def get_states(self) -> list[dict]:
        return self._api.rest_get("/api/states")

    def get_config(self) -> dict:
        return self._api.rest_get("/api/config")

    def get_services(self) -> list[dict]:
        return self._api.rest_get("/api/services")

    def get_entities(self) -> list[dict]:
        return self._api.ws_call("config/entity_registry/list")

    def get_devices(self) -> list[dict]:
        return self._api.ws_call("config/device_registry/list")

    def get_areas(self) -> list[dict]:
        return self._api.ws_call("config/area_registry/list")

    def get_labels(self) -> list[dict]:
        return self._api.ws_call("config/label_registry/list")
