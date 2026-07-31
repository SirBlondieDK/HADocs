from __future__ import annotations

from pathlib import Path

from .matcher import DeviceMatcher
from .models import DeviceMatch, Organization
from .repository import HUDDRepository


class HUDDService:
    def __init__(self, database: str | Path | None = None) -> None:
        self.repository = HUDDRepository(database)
        self.matcher = DeviceMatcher(self.repository)

    def get_organization(self, name_or_id: str) -> Organization | None:
        return self.repository.get_organization(name_or_id)

    def search_organizations(self, query: str, limit: int = 25) -> list[Organization]:
        return self.repository.search_organizations(query, limit)

    def find_device(
        self,
        *,
        manufacturer: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        product_name: str | None = None,
        hardware_revision: str | None = None,
        region: str | None = None,
        identifiers: dict[str, str] | None = None,
    ) -> DeviceMatch:
        return self.matcher.match(
            manufacturer=manufacturer,
            brand=brand,
            model=model,
            product_name=product_name,
            hardware_revision=hardware_revision,
            region=region,
            identifiers=identifiers,
        )


_default_service: HUDDService | None = None


def _service() -> HUDDService:
    global _default_service
    if _default_service is None:
        _default_service = HUDDService()
    return _default_service


def get_organization(name_or_id: str) -> Organization | None:
    return _service().get_organization(name_or_id)


def search_organizations(query: str, limit: int = 25) -> list[Organization]:
    return _service().search_organizations(query, limit)


def find_device(**identity) -> DeviceMatch:
    return _service().find_device(**identity)
