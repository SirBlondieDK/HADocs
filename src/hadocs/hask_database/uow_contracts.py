from __future__ import annotations

from dataclasses import dataclass

from .repository_contracts import RepositoryOwner


@dataclass(frozen=True, slots=True)
class UnitOfWorkContract:
    name: str
    required_input: tuple[str, ...]
    repository_owners: tuple[RepositoryOwner, ...]
    permitted_starting_states: tuple[str, ...]
    permitted_terminal_states: tuple[str, ...]
    validations: tuple[str, ...]
    atomic_writes: tuple[str, ...]
    semantic_result: tuple[str, ...]
    equivalent_retry: str
    conflicting_retry: str


SCAN_COMPLETION_CONTRACT = UnitOfWorkContract(
    name="scan_completion",
    required_input=(
        "scan_run_id",
        "expected_installation_id",
        "completion_idempotency_key",
        "terminal_at",
        "terminal_status",
        "completeness",
        "safe_error_code",
        "capability_outcomes",
        "observation_ids",
    ),
    repository_owners=(
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    ),
    permitted_starting_states=("RUNNING",),
    permitted_terminal_states=("SUCCEEDED", "FAILED", "INTERRUPTED", "CANCELLED"),
    validations=(
        "scan_exists_and_installation_matches",
        "running_or_equivalent_terminal_state",
        "capability_identity_and_shape",
        "observation_ownership_and_complete_reference_set",
        "audit_identity_and_links",
        "equivalent_retry_artifacts",
    ),
    atomic_writes=(
        "scan_capability_outcome inserts",
        "SCAN_TERMINATED audit_record insert",
        "audit_subject_link insert",
        "ordered audit_evidence_link inserts",
        "scan_run terminal transition",
    ),
    semantic_result=(
        "scan_run_id",
        "terminal state",
        "capability_outcome_ids",
        "terminal_audit_id",
        "observation_ids",
    ),
    equivalent_retry="return persisted IDs without INSERT or UPDATE",
    conflicting_retry="raise IDEMPOTENCY_CONFLICT before any write",
)


ENTITY_PERSISTENCE_CONTRACT = UnitOfWorkContract(
    name="entity_persistence",
    required_input=(
        "installation_id",
        "context_id",
        "scan_run_id",
        "observation_id",
        "event_at",
        "entities",
    ),
    repository_owners=(
        RepositoryOwner.LOGICAL_INSTALLATION,
        RepositoryOwner.COLLISION_REGISTRY,
        RepositoryOwner.ENTITY,
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    ),
    permitted_starting_states=("RUNNING",),
    permitted_terminal_states=(
        "ACTIVE",
        "REMOVED",
    ),
    validations=(
        "active_identity_context_and_protected_secret",
        "running_scan_and_observation_ownership",
        "exact_ca001_entity_derivation",
        "installation_wide_collision_registry",
        "equivalent_identity_and_lifecycle_replay",
        "explicit_frozen_lifecycle_transition",
    ),
    atomic_writes=(
        "collision registry insert when absent",
        "identity registration audit and insert",
        "entity insert",
        "initial or structural lifecycle event and audit",
        "entity current-state insert or transition",
        "audit subject and evidence links",
    ),
    semantic_result=(
        "identity registration IDs",
        "entity IDs",
        "current-state IDs",
        "source lifecycle-event IDs",
        "opaque entity references",
    ),
    equivalent_retry="return persisted IDs without INSERT or UPDATE",
    conflicting_retry="raise IDEMPOTENCY_CONFLICT and roll back every entity write",
)


RELATIONSHIP_PERSISTENCE_CONTRACT = UnitOfWorkContract(
    name="relationship_persistence",
    required_input=(
        "installation_id",
        "context_id",
        "scan_run_id",
        "observation_id",
        "event_at",
        "relationships",
    ),
    repository_owners=(
        RepositoryOwner.LOGICAL_INSTALLATION,
        RepositoryOwner.COLLISION_REGISTRY,
        RepositoryOwner.ENTITY,
        RepositoryOwner.RELATIONSHIP,
        RepositoryOwner.SCAN_RUN,
        RepositoryOwner.OBSERVATION,
        RepositoryOwner.AUDIT,
    ),
    permitted_starting_states=("RUNNING",),
    permitted_terminal_states=("CURRENT", "CURRENT_ABSENT"),
    validations=(
        "active_identity_context_and_protected_secret",
        "running_scan_and_observation_ownership",
        "persisted_same_context_source_entity",
        "exact_target_reference_contract",
        "ordered_frozen_relationship_identity",
        "equivalent_identity_and_lifecycle_replay",
        "explicit_frozen_lifecycle_transition",
    ),
    atomic_writes=(
        "target collision registration and audit when required",
        "relationship insert when absent",
        "initial or explicit lifecycle event and audit",
        "relationship current-state insert or transition",
        "audit subject and evidence links",
    ),
    semantic_result=(
        "relationship IDs",
        "current-state IDs",
        "source lifecycle-event IDs",
        "public relationship references",
        "protected endpoint references",
    ),
    equivalent_retry="return persisted IDs without INSERT or UPDATE",
    conflicting_retry=(
        "raise IDEMPOTENCY_CONFLICT and roll back every relationship write"
    ),
)
