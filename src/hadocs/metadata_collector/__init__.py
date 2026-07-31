"""Generic Metadata Collector infrastructure frozen by DF-001."""

from .bootstrap import CollectorInfrastructure, bootstrap
from .contract import (
    COLLECTOR_NAME,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    CapabilityRecord,
    CapabilityStatus,
    Observation,
    Producer,
    Relationship,
    Snapshot,
    Source,
    Stability,
)
from .lifecycle import CollectorConfig, CollectorLifecycle, ExecutionContext, LifecycleState
from .registry import CapabilityDefinition, CapabilityRegistry, ContractRegistry
from .versioning import ContractRegistration, VersionNegotiator

__all__ = [
    "COLLECTOR_NAME",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CapabilityDefinition",
    "CapabilityRecord",
    "CapabilityRegistry",
    "CapabilityStatus",
    "CollectorConfig",
    "CollectorInfrastructure",
    "CollectorLifecycle",
    "ContractRegistration",
    "ContractRegistry",
    "ExecutionContext",
    "LifecycleState",
    "Observation",
    "Producer",
    "Relationship",
    "Snapshot",
    "Source",
    "Stability",
    "VersionNegotiator",
    "bootstrap",
]
