from __future__ import annotations

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import os
from pathlib import Path
import unicodedata
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

if TYPE_CHECKING:
    from hadocs.core.models import InstallationModel
    from hadocs.application.hask_candidate_evidence import (
        CandidateEvidenceBridgeResult,
    )


OBSERVATION_KEY = "hadocs.normalized-counts.v1"
CONTRACT_VERSION = "hadocs.normalized-counts.v1"
IMPLEMENTATION_VERSION = "hadocs-product-integration-v1"
CAPABILITY_ID = "hadocs.normalized-counts.v1"


class OperationalDatabasePersistenceState(str, Enum):
    DISABLED = "disabled"
    COMPLETED = "completed"


class DatabaseIdentityInitializationState(str, Enum):
    INITIALIZED = "initialized"
    ALREADY_INITIALIZED = "already_initialized"


@dataclass(frozen=True, slots=True)
class DatabaseIdentityInitializationResult:
    state: DatabaseIdentityInitializationState


@dataclass(frozen=True, slots=True)
class OperationalDatabaseOperation:
    """Stable caller intent for one scan, injectable for deterministic retry."""

    identity: str
    started_at: str
    terminal_at: str

    def __post_init__(self) -> None:
        for name in ("identity", "started_at", "terminal_at"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"operation {name} must be non-empty text")

    @classmethod
    def new(
        cls,
        *,
        clock: Callable[[], str] | None = None,
    ) -> OperationalDatabaseOperation:
        now = (clock or _utc_now)()
        return cls(
            identity=f"{now}:{uuid4().hex}",
            started_at=now,
            terminal_at=now,
        )


@dataclass(frozen=True, slots=True)
class OperationalDatabasePersistenceResult:
    """Small explicit application result without exposing database internals."""

    state: OperationalDatabasePersistenceState
    operation_id: str | None = None
    replay_state: str | None = None
    installation_id: int | None = None
    context_id: int | None = None
    scan_run_id: int | None = None
    observation_ids: tuple[int, ...] = ()
    entity_ids: tuple[int, ...] = ()
    entity_references: tuple[str, ...] = ()
    eligible_relationship_count: int = 0
    persisted_relationship_count: int = 0
    ineligible_relationship_count: int = 0
    capability_outcome_ids: tuple[int, ...] = ()
    completion_audit_id: int | None = None
    hask_candidate_evidence: CandidateEvidenceBridgeResult | None = None

    def __post_init__(self) -> None:
        completed = self.state is OperationalDatabasePersistenceState.COMPLETED
        required = (
            self.operation_id,
            self.replay_state,
            self.installation_id,
            self.context_id,
            self.scan_run_id,
            self.completion_audit_id,
        )
        if completed != all(value is not None for value in required):
            raise ValueError("persistence state and persisted result IDs must agree")
        if not completed and (
            self.observation_ids
            or self.entity_ids
            or self.entity_references
            or self.eligible_relationship_count
            or self.persisted_relationship_count
            or self.ineligible_relationship_count
            or self.capability_outcome_ids
            or self.hask_candidate_evidence is not None
        ):
            raise ValueError("disabled persistence cannot contain database IDs")
        counts = (
            self.eligible_relationship_count,
            self.persisted_relationship_count,
            self.ineligible_relationship_count,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in counts
        ):
            raise ValueError("relationship persistence counts must be non-negative integers")
        if self.persisted_relationship_count > self.eligible_relationship_count:
            raise ValueError("persisted relationship count exceeds eligible intent")


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _enabled_value(config: Mapping[str, object]) -> object | None:
    if "HADOCS_HASK_DATABASE_ENABLED" in os.environ:
        return os.environ["HADOCS_HASK_DATABASE_ENABLED"]
    return config.get("hask_database_enabled")


def _database_requested(config: Mapping[str, object]) -> bool:
    value = _enabled_value(config)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    raise ValueError("hask_database_enabled must be a boolean value")


def _configured_text(
    config: Mapping[str, object], environment_name: str, config_name: str
) -> str:
    raw = os.environ.get(environment_name, config.get(config_name, ""))
    return "" if raw is None else str(raw).strip()


def operational_secret_provider(
    config: Mapping[str, object],
    *,
    identity_backend: str | None,
    injected: object | None,
):
    from hadocs.hask_database import SecretProvider, select_secret_provider

    configured_backend = _configured_text(
        config,
        "HADOCS_HASK_DATABASE_SECRET_BACKEND",
        "hask_database_secret_backend",
    ) or None
    selected_backend = identity_backend or configured_backend
    if (
        identity_backend is not None
        and configured_backend is not None
        and configured_backend != identity_backend
    ):
        raise ValueError("configured protected backend disagrees with database identity")

    if injected is not None:
        provider = injected
        if not isinstance(provider, SecretProvider):
            raise TypeError("secret provider does not satisfy the protected contract")
        provider_kind = getattr(provider, "backend_kind", None)
        if selected_backend is not None and provider_kind != selected_backend:
            raise ValueError("protected provider backend disagrees with database identity")
        return provider

    from hadocs.utils.config import persistent_config_root

    credential_path = _configured_text(
        config,
        "HADOCS_HASK_CREDENTIAL_STORE_PATH",
        "hask_database_credential_store_path",
    ) or None
    return select_secret_provider(
        backend_kind=selected_backend,
        config_root=persistent_config_root(),
        configured_path=credential_path,
    )


def initialize_operational_database_identity(
    config: Mapping[str, object],
    *,
    secret_provider: object | None = None,
    uuid_factory: Callable[[], object] = uuid4,
    save: Callable[[dict[str, object]], None] | None = None,
) -> tuple[DatabaseIdentityInitializationResult, dict[str, object]]:
    """Explicitly initialize persistent non-secret identity metadata.

    Secret creation is delegated to the protected provider and happens only
    after complete absence of identity metadata has been established.
    """

    from hadocs.hask_database import (
        HaskDatabaseIdentityConfig,
        canonical_installation_uuid,
        derive_installation_scope,
    )

    path_text = _configured_text(
        config, "HADOCS_HASK_DATABASE_PATH", "hask_database_path"
    )
    if not path_text:
        raise ValueError("an explicit operational database path is required")
    from hadocs.platform.paths import AppPaths

    path = AppPaths.discover().resolve_data_path(path_text)
    if path.name.lower() == "hudd.sqlite":
        raise ValueError("the operational database must not reuse hudd.sqlite")

    installation_ref = _configured_text(
        config,
        "HADOCS_HASK_DATABASE_INSTALLATION_REF",
        "hask_database_installation_ref",
    )
    if not installation_ref:
        raise ValueError("an explicit non-secret installation reference is required")
    if (
        len(installation_ref) > 256
        or any(ord(character) < 32 for character in installation_ref)
        or "://" in installation_ref
        or "/" in installation_ref
        or "\\" in installation_ref
    ):
        raise ValueError("installation reference is invalid")

    identity = HaskDatabaseIdentityConfig.from_mapping(config)
    provider = operational_secret_provider(
        config,
        identity_backend=None if identity is None else identity.secret_backend,
        injected=secret_provider,
    )
    if identity is not None:
        provider.load(identity.secret_handle, identity.secret_generation)
        return (
            DatabaseIdentityInitializationResult(
                DatabaseIdentityInitializationState.ALREADY_INITIALIZED
            ),
            dict(config),
        )

    raw_uuid = canonical_installation_uuid(str(uuid_factory()))
    scope = derive_installation_scope(raw_uuid)
    from hadocs.hask_database import CredentialStoreSecretProvider

    expected_handle = CredentialStoreSecretProvider.handle_for(scope, 1)
    backend_kind = getattr(provider, "backend_kind", None)
    if not isinstance(backend_kind, str):
        raise ValueError("protected provider did not identify its backend kind")
    guard = getattr(provider, "initialization_guard", None)
    with (guard() if guard is not None else nullcontext()):
        pending = dict(config)
        pending.update(
            {
                "hask_database_identity_version": 1,
                "hask_database_installation_uuid": raw_uuid,
                "hask_database_installation_scope": scope,
                "hask_database_secret_handle": expected_handle,
                "hask_database_secret_generation": 1,
                "hask_database_identity_state": "initializing",
                "hask_database_secret_backend": backend_kind,
            }
        )
        if save is not None:
            save(pending)

        reference = provider.create(scope)
        if reference.generation != 1 or reference.handle != expected_handle:
            try:
                provider.destroy(reference.handle, reference.generation)
            finally:
                raise ValueError("protected provider returned incompatible identity metadata")
        provider.load(reference.handle, reference.generation)

        identity = HaskDatabaseIdentityConfig(
            version=1,
            installation_uuid=raw_uuid,
            installation_scope=scope,
            secret_handle=reference.handle,
            secret_generation=reference.generation,
            state="initialized",
            secret_backend=backend_kind,
        )
        updated = dict(config)
        updated.update(identity.as_config_values())
        if save is not None:
            save(updated)
    return (
        DatabaseIdentityInitializationResult(
            DatabaseIdentityInitializationState.INITIALIZED
        ),
        updated,
    )


def _configured_operation(
    config: Mapping[str, object],
) -> OperationalDatabaseOperation | None:
    def value(environment_name: str, config_name: str) -> str:
        raw = os.environ.get(environment_name, config.get(config_name, ""))
        return "" if raw is None else str(raw).strip()

    identity = value(
        "HADOCS_HASK_DATABASE_OPERATION_ID",
        "hask_database_operation_id",
    )
    started_at = value(
        "HADOCS_HASK_DATABASE_OPERATION_STARTED_AT",
        "hask_database_operation_started_at",
    )
    terminal_at = value(
        "HADOCS_HASK_DATABASE_OPERATION_TERMINAL_AT",
        "hask_database_operation_terminal_at",
    )
    if not any((identity, started_at, terminal_at)):
        return None
    if not all((identity, started_at, terminal_at)):
        raise ValueError(
            "configured operation identity requires started_at and terminal_at"
        )
    return OperationalDatabaseOperation(identity, started_at, terminal_at)


def _aggregate_payload(model: InstallationModel) -> dict[str, int]:
    """Return the complete persisted JSON contract.

    The sole observation contains exactly four integer counts: ``areas``,
    ``devices``, ``entities`` and ``integrations``.  No model identifiers,
    names, states, raw records, URLs, credentials, findings, recommendations,
    HASK results or Health Score values are inspected or persisted.
    """

    return {
        "areas": len(model.areas),
        "devices": len(model.devices),
        "entities": len(model.entities),
        "integrations": len(model.integrations),
    }


def _native_status_requested(config: Mapping[str, object]) -> bool:
    value = config.get("hask_native_integration_status_enabled", False)
    if not isinstance(value, bool):
        raise ValueError(
            "hask_native_integration_status_enabled must be a boolean value"
        )
    return value


def _native_status_payloads(
    model: InstallationModel,
) -> tuple[tuple[str, str, dict[str, object]], ...]:
    from hadocs.collectors.native_integration_status import (
        NativeIntegrationStatusError,
        observation_key,
        validate_domain_observation,
    )

    raw = model.raw.get("native_integration_status", ())
    if not isinstance(raw, (list, tuple)):
        raise NativeIntegrationStatusError(
            "native integration-status collection has an invalid shape"
        )
    normalized: list[tuple[str, str, dict[str, object]]] = []
    domains: set[str] = set()
    for value in raw:
        payload = validate_domain_observation(value)
        domain = str(payload["domain"])
        if domain in domains:
            raise NativeIntegrationStatusError(
                "native integration-status collection repeats a domain"
            )
        domains.add(domain)
        normalized.append((observation_key(domain), str(payload["observed_at"]), payload))
    return tuple(sorted(normalized, key=lambda item: item[0]))


def _relationship_candidates(model: InstallationModel) -> tuple[object, ...]:
    """Build Batch 4B0 candidates only from the normalized typed entity shape.

    Older synthetic callers used string values in ``InstallationModel.entities``.
    Those values never represented persistable entity facts and therefore produce
    no relationship candidates.
    """

    entity_values = tuple(model.entities.values())
    required = ("entity_id", "platform", "device_id", "area_id", "registry")
    if any(
        not all(hasattr(entity, attribute) for attribute in required)
        for entity in entity_values
    ):
        return ()
    from hadocs.core.relationships import build_relationship_candidates

    return build_relationship_candidates(model)


def persist_operational_database(
    model: InstallationModel,
    config: Mapping[str, object],
    *,
    operation: OperationalDatabaseOperation | None = None,
    secret_provider: object | None = None,
) -> OperationalDatabasePersistenceResult:
    """Persist and complete one privacy-safe normalized scan summary.

    Disabled mode returns before importing ``hadocs.hask_database``.  Enabled
    failures propagate to the shared application boundary and never mutate the
    supplied normalized or analytical model.
    """

    if not _database_requested(config):
        return OperationalDatabasePersistenceResult(
            state=OperationalDatabasePersistenceState.DISABLED
        )

    from hadocs.hask_database import (
        CapabilityOutcomeInput,
        HaskDatabaseApplicationConfig,
        HaskDatabaseService,
        HaskSQLiteConnectionFactory,
        EntityPersistenceInput,
        EntityPersistenceRequest,
        ObservationInput,
        OperationalReplayState,
        OperationalSliceRequest,
        RelationshipPersistenceInput,
        RelationshipPersistenceRequest,
        ScanCompletionIntent,
    )

    settings = HaskDatabaseApplicationConfig.from_application_config(config)
    assert settings.installation_ref is not None
    assert settings.identity is not None
    provider = operational_secret_provider(
        config,
        identity_backend=settings.identity.secret_backend,
        injected=secret_provider,
    )
    provider.load(
        settings.identity.secret_handle,
        settings.identity.secret_generation,
    )
    selected_operation = operation or _configured_operation(config)
    if selected_operation is None:
        selected_operation = OperationalDatabaseOperation.new()

    observation = ObservationInput(
        observation_key=OBSERVATION_KEY,
        taxonomy_class="B",
        authority_class="STRUCTURED_CONTEXT_DEPENDENT",
        observed_at=selected_operation.started_at,
        payload=_aggregate_payload(model),
        privacy_class="LOCAL_ONLY",
        retention_policy="RETAIN_UNTIL_SUPERSEDED",
    )
    observations = [observation]
    if _native_status_requested(config):
        observations.extend(
            ObservationInput(
                observation_key=key,
                taxonomy_class="B",
                authority_class="AUTHORITATIVE_FACT",
                observed_at=observed_at,
                payload=payload,
                privacy_class="LOCAL_ONLY",
                retention_policy="RETAIN_UNTIL_SUPERSEDED",
            )
            for key, observed_at, payload in _native_status_payloads(model)
        )
    start_request = OperationalSliceRequest(
        recovery_set_ref=f"hadocs:installation:{settings.installation_ref}",
        installation_scope=settings.identity.installation_scope,
        secret_handle=settings.identity.secret_handle,
        secret_generation=settings.identity.secret_generation,
        context_format_version=1,
        scan_idempotency_key=f"hadocs:normal-scan:{selected_operation.identity}",
        started_at=selected_operation.started_at,
        implementation_version=IMPLEMENTATION_VERSION,
        contract_version=CONTRACT_VERSION,
        observations=tuple(observations),
    )
    completion_intent = ScanCompletionIntent(
        completion_idempotency_key=(
            f"hadocs:normal-scan-completion:{selected_operation.identity}"
        ),
        terminal_at=selected_operation.terminal_at,
        terminal_status="SUCCEEDED",
        completeness="COMPLETE",
        safe_error_code=None,
        capabilities=(
            CapabilityOutcomeInput(
                capability_id=CAPABILITY_ID,
                status="SUCCEEDED",
                retryable=None,
                safe_error_code=None,
                observation_contribution=True,
                completeness_contribution="COMPLETE",
            ),
        ),
    )

    service = HaskDatabaseService(
        HaskSQLiteConnectionFactory(settings.database),
        provider,
        require_protected_identity=True,
    )
    service.startup()
    try:
        service.validate_operational_identity(start_request)
        replay = service.start_or_replay_operational_slice(
            start_request,
            completion_intent=completion_intent,
        )
        if replay.state is OperationalReplayState.EXISTING_TERMINAL:
            completion = replay.completion
            assert completion is not None
            persisted_entities = service.list_entities_for_installation(
                replay.operational_slice.installation_id
            )
            entity_ids = tuple(int(item["id"]) for item in persisted_entities)
            entity_references = tuple(
                str(item["opaque_reference"]) for item in persisted_entities
            )
            relationship_candidates = _relationship_candidates(model)
            eligible_relationship_count = sum(
                item.persistence_eligible for item in relationship_candidates
            )
            ineligible_relationship_count = (
                len(relationship_candidates) - eligible_relationship_count
            )
            persisted_relationship_count = sum(
                item.get("current_status") == "CURRENT"
                for item in service.list_relationships_for_installation(
                    replay.operational_slice.installation_id
                )
            )
        else:
            entity_result = None
            normalized_entities = tuple(
                sorted(
                    (
                        entity.entity_id
                        for entity in model.entities.values()
                        if isinstance(getattr(entity, "entity_id", None), str)
                    ),
                    key=lambda value: unicodedata.normalize("NFC", value),
                )
            )
            if normalized_entities:
                entity_result = service.persist_entities(EntityPersistenceRequest(
                    installation_id=replay.operational_slice.installation_id,
                    context_id=replay.operational_slice.context_id,
                    scan_run_id=replay.operational_slice.scan_run_id,
                    observation_id=replay.operational_slice.observation_ids[0],
                    event_at=selected_operation.started_at,
                    entities=tuple(
                        EntityPersistenceInput(
                            entity_key=f"entity-{ordinal:06d}",
                            raw_entity_id=raw_entity_id,
                        )
                        for ordinal, raw_entity_id in enumerate(normalized_entities)
                    ),
                ))
            relationship_candidates = _relationship_candidates(model)
            eligible_candidates = tuple(
                item for item in relationship_candidates if item.persistence_eligible
            )
            eligible_relationship_count = len(eligible_candidates)
            ineligible_relationship_count = (
                len(relationship_candidates) - eligible_relationship_count
            )
            if eligible_candidates:
                relationship_result = service.persist_relationships(
                    RelationshipPersistenceRequest(
                        installation_id=replay.operational_slice.installation_id,
                        context_id=replay.operational_slice.context_id,
                        scan_run_id=replay.operational_slice.scan_run_id,
                        observation_id=replay.operational_slice.observation_ids[0],
                        event_at=selected_operation.started_at,
                        relationships=tuple(
                            RelationshipPersistenceInput(
                                relationship_key=f"relationship-{ordinal:06d}",
                                raw_source_entity_id=(
                                    candidate.source_entity_identity_input
                                ),
                                predicate=candidate.predicate.value,
                                target_kind=candidate.target_kind.value,
                                raw_target_id=candidate.target_identity_input or "",
                            )
                            for ordinal, candidate in enumerate(eligible_candidates)
                        ),
                    )
                )
                persisted_relationship_count = len(
                    relationship_result.relationships
                )
            else:
                persisted_relationship_count = 0
            completion = service.complete_scan(
                completion_intent.bind(replay.operational_slice)
            )
            if entity_result is None:
                entity_ids = ()
                entity_references = ()
            else:
                entity_ids = tuple(item.entity_id for item in entity_result.entities)
                entity_references = tuple(
                    item.opaque_reference for item in entity_result.entities
                )
        candidate_evidence = None
        bridge_enabled = config.get("hask_candidate_evidence_enabled", False)
        hask_enabled = config.get("hask_enabled", False)
        if not isinstance(bridge_enabled, bool) or not isinstance(hask_enabled, bool):
            raise ValueError("HASK candidate bridge feature flags must be boolean")
        if bridge_enabled and hask_enabled:
            from hadocs.application.hask_candidate_evidence import (
                build_candidate_evidence_bridge,
            )

            candidate_evidence = build_candidate_evidence_bridge(
                service=service,
                operational_slice=replay.operational_slice,
                completion=completion,
                config=config,
            )
        return OperationalDatabasePersistenceResult(
            state=OperationalDatabasePersistenceState.COMPLETED,
            operation_id=selected_operation.identity,
            replay_state=replay.state.value,
            installation_id=replay.operational_slice.installation_id,
            context_id=replay.operational_slice.context_id,
            scan_run_id=replay.operational_slice.scan_run_id,
            observation_ids=replay.operational_slice.observation_ids,
            entity_ids=entity_ids,
            entity_references=entity_references,
            eligible_relationship_count=eligible_relationship_count,
            persisted_relationship_count=persisted_relationship_count,
            ineligible_relationship_count=ineligible_relationship_count,
            capability_outcome_ids=completion.capability_outcome_ids,
            completion_audit_id=completion.audit_id,
            hask_candidate_evidence=candidate_evidence,
        )
    finally:
        service.shutdown()
