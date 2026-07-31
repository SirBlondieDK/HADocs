from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Organization:
    hudd_id: str
    canonical_name: str
    entity_type: str
    category: str | None = None
    connection_class: str = "UKENDT"
    review_status: str = "seed"
    support_codes: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class Device:
    hudd_id: str | None
    product_name: str
    model: str | None
    manufacturer: str | None
    brand: str | None
    hardware_revision: str | None = None
    region: str | None = None
    product_family: str | None = None
    lifecycle_status: str = "unknown"
    review_status: str = "seed"
    aliases: list[str] = field(default_factory=list)
    identifiers: dict[str, list[str]] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DeviceIdentity:
    manufacturer: str | None = None
    brand: str | None = None
    model: str | None = None
    product_name: str | None = None
    hardware_revision: str | None = None
    region: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DeviceMatch:
    device: Device | None
    confidence: float
    level: str
    reason: str
    matched_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
