from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class RepositoryOwner(str, Enum):
    LOGICAL_INSTALLATION = "LogicalInstallationRepository"
    COLLISION_REGISTRY = "CollisionRegistryRepository"
    ENTITY = "EntityRepository"
    RELATIONSHIP = "RelationshipRepository"
    SCAN_RUN = "ScanRunRepository"
    OBSERVATION = "ObservationRepository"
    COMPATIBILITY_DECISION = "CompatibilityDecisionRepository"
    AUDIT = "AuditRepository"
    VERSION_STATE = "VersionStateRepository"
    MIGRATION_STATE = "MigrationStateRepository"


FROZEN_OWNERSHIP: dict[RepositoryOwner, frozenset[str]] = {
    RepositoryOwner.LOGICAL_INSTALLATION: frozenset({
        "logical_installation", "installation_context", "authoritative_declaration",
        "protected_provenance_reference", "clone_decision", "activation_outcome",
    }),
    RepositoryOwner.COLLISION_REGISTRY: frozenset({"collision_registry", "identity_registration"}),
    RepositoryOwner.ENTITY: frozenset({"entity", "entity_current_state", "entity_lifecycle_event"}),
    RepositoryOwner.RELATIONSHIP: frozenset({
        "relationship", "relationship_current_state", "relationship_lifecycle_event",
    }),
    RepositoryOwner.SCAN_RUN: frozenset({"scan_run", "scan_capability_outcome"}),
    RepositoryOwner.OBSERVATION: frozenset({"observation", "observation_subject_link"}),
    RepositoryOwner.COMPATIBILITY_DECISION: frozenset({"compatibility_decision"}),
    RepositoryOwner.AUDIT: frozenset({"audit_record", "audit_evidence_link", "audit_subject_link"}),
    RepositoryOwner.VERSION_STATE: frozenset({"version_state"}),
    RepositoryOwner.MIGRATION_STATE: frozenset({"migration_state", "migration_attempt"}),
}


@dataclass(frozen=True, slots=True)
class RepositoryDescriptor:
    owner: RepositoryOwner
    tables: frozenset[str]
    lifetime: str = "UNIT_OF_WORK"
    permits_business_persistence: bool = False


@runtime_checkable
class RepositoryContract(Protocol):
    @property
    def descriptor(self) -> RepositoryDescriptor: ...


def validate_frozen_ownership(actual_tables: frozenset[str]) -> None:
    if set(FROZEN_OWNERSHIP) != set(RepositoryOwner):
        raise ValueError("exactly the ten frozen repository owners are required")
    flattened = [table for tables in FROZEN_OWNERSHIP.values() for table in tables]
    if len(flattened) != len(set(flattened)):
        raise ValueError("a table has more than one repository owner")
    if frozenset(flattened) != actual_tables:
        raise ValueError("repository ownership does not match the frozen schema")
