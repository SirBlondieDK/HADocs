"""Dependency-injected infrastructure bootstrap; no API client is created."""

from __future__ import annotations

from dataclasses import dataclass

from .lifecycle import CollectorConfig, CollectorLifecycle
from .normalization import Normalizer
from .privacy import PrivacyTransformer
from .registry import CapabilityRegistry, ContractRegistry
from .serialization import SnapshotSerializer
from .versioning import ContractRegistration, VersionNegotiator


@dataclass(frozen=True, slots=True)
class CollectorInfrastructure:
    lifecycle: CollectorLifecycle
    capabilities: CapabilityRegistry
    contract_registry: ContractRegistry
    privacy: PrivacyTransformer
    versioning: VersionNegotiator
    contract: ContractRegistration


def bootstrap(config: CollectorConfig | None = None) -> CollectorInfrastructure:
    capabilities = CapabilityRegistry()
    contract_registry = ContractRegistry()
    normalizer = Normalizer(contract_registry)
    serializer = SnapshotSerializer(normalizer)
    versioning = VersionNegotiator()
    lifecycle = CollectorLifecycle(config, capabilities, normalizer, serializer)
    return CollectorInfrastructure(
        lifecycle=lifecycle,
        capabilities=capabilities,
        contract_registry=contract_registry,
        privacy=PrivacyTransformer(),
        versioning=versioning,
        contract=versioning.registration(),
    )

