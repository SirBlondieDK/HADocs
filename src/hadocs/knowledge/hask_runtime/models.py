from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class RuntimeBundle:
    checksum: str
    contract_version: str
    manifest: Mapping[str, Any]
    artifacts: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class RuntimeDiagnostics:
    enabled: bool
    lifecycle_state: str
    active: bool
    discovery_status: str
    discovery_source: str
    bundle_path: str | None
    bundle_version: str | None
    checksum_status: str
    compatibility: str
    validation_status: str
    cache_status: str
    trust_status: str
    graceful_degradation_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TypedMatcherContract:
    record_ref: str
    matcher_id: str
    version: str
    platform_scope: tuple[str, ...]
    observation_types: tuple[str, ...]
    required_fields: tuple[tuple[str, str], ...]
    evidence_target: str
