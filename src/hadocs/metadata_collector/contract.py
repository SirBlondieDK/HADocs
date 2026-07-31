"""Immutable contract types for DF-001 contract version 1.0.0."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

CONTRACT_NAME = "hadocs-generic-metadata"
CONTRACT_VERSION = "1.0.0"
COLLECTOR_NAME = "Generic Metadata Collector"


class CapabilityStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    PERMISSION_DENIED = "permission_denied"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"
    AUTHENTICATION_EXPIRED = "authentication_expired"


class Stability(str, Enum):
    DOCUMENTED_UNVERSIONED = "documented_unversioned"
    DOCUMENTED_COMPACT_OPTIONAL = "documented_compact_optional"
    CONTRACT_STABLE = "contract_stable"


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class Producer:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class Source:
    core_version: str | None
    api_surfaces: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    capability_id: str
    status: CapabilityStatus
    observed_at: str
    safe_error_code: str | None = None
    retryable: bool | None = None


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    category: str
    canonical_key: str
    source_capability: str
    source_api: str
    observed_at: str
    fields: Mapping[str, Any]
    privacy_treatment: str
    stability: Stability
    relationships: tuple[str, ...] = ()
    source_core_version: str | None = None
    scope: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", freeze(self.fields))


@dataclass(frozen=True, slots=True)
class Relationship:
    relationship_id: str
    predicate: str
    source_ref: str
    target_ref: str
    source_capability: str
    observed_at: str
    resolution: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    snapshot_id: str
    observed_at: str
    producer: Producer
    source: Source
    capabilities: tuple[CapabilityRecord, ...] = field(default_factory=tuple)
    observations: tuple[Observation, ...] = field(default_factory=tuple)
    relationships: tuple[Relationship, ...] = field(default_factory=tuple)

    @property
    def contract_name(self) -> str:
        return CONTRACT_NAME

    @property
    def contract_version(self) -> str:
        return CONTRACT_VERSION


def _public_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            item.name: _public_value(getattr(value, item.name))
            for item in fields(value)
            if getattr(value, item.name) is not None
        }
    if isinstance(value, Mapping):
        return {str(key): _public_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_public_value(item) for item in value]
    return value


def public_mapping(snapshot: Snapshot) -> dict[str, Any]:
    """Return only fields frozen in the public producer contract."""
    value = _public_value(snapshot)
    value["contract_name"] = CONTRACT_NAME
    value["contract_version"] = CONTRACT_VERSION
    return value
