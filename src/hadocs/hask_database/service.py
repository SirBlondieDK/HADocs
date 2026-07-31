from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import re
import struct
import unicodedata
from typing import Callable, Mapping, cast

from .coordination import canonical_intent_digest
from .connection import HaskSQLiteConnectionFactory, ManagedSQLiteConnection
from .errors import (
    HaskDatabaseError,
    IdempotencyConflictError,
    NotFoundError,
    ValidationFailureError,
)
from .migration_chain import initialize_batch2_schema
from .repositories import (
    AuditRepository,
    CollisionRegistryRepository,
    EntityRepository,
    LogicalInstallationRepository,
    ObservationRepository,
    RelationshipRepository,
    ScanRunRepository,
)
from .repository_contracts import RepositoryOwner
from .schema import verify_schema
from .secrets import NullSecretProvider, SecretProvider
from .transactions import SerializedTransactionManager
from .uow_contracts import (
    ENTITY_PERSISTENCE_CONTRACT,
    RELATIONSHIP_PERSISTENCE_CONTRACT,
    SCAN_COMPLETION_CONTRACT,
)
from .validators import (
    ENTITY_PRESENT_REASON,
    RELATIONSHIP_PRESENT_REASON,
    RELATIONSHIP_RECREATION_REASON,
    RELATIONSHIP_REMOVAL_REASON,
    SCAN_AUDIT_EVIDENCE_ROLE,
    SCAN_AUDIT_SUBJECT_ROLE,
    validate_completion_intent,
    validate_entity_intent,
    validate_entity_transition,
    validate_no_partial_completion,
    validate_observation_ownership,
    validate_relationship_intent,
    validate_relationship_transition,
    validate_retry_artifacts,
    validate_scan_state,
)


CURRENT_SCHEMA_VERSION = 8
_CA001_SCOPE_PATTERN = re.compile(r"is1_[0-9a-f]{64}")
_CA001_DOMAIN = b"HASK/HADOCS/OPAQUE-REFERENCE/HMAC-SHA-256"
_PROTECTED_REFERENCE_PATTERN = re.compile(
    r"refh1_(entity|device|area|label)_[0-9a-f]{64}"
)
_OBSERVATION_REFERENCE_PATTERN = re.compile(r"obs1_[0-9a-f]{64}")
_RELATIONSHIP_REFERENCE_PATTERN = re.compile(r"rel1_[0-9a-f]{64}")
_CA001_REFERENCE_KINDS = frozenset({"entity", "device", "area", "label"})


class ServiceState(str, Enum):
    DISABLED = "disabled"
    ACTIVE = "active"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class ServiceStatus:
    state: ServiceState


@dataclass(frozen=True, slots=True)
class ObservationInput:
    observation_key: str
    taxonomy_class: str
    authority_class: str
    observed_at: str
    payload: Mapping[str, object]
    privacy_class: str
    retention_policy: str
    provenance_ref: str | None = None


@dataclass(frozen=True, slots=True)
class OperationalSliceRequest:
    recovery_set_ref: str
    installation_scope: str
    secret_handle: str
    secret_generation: int
    context_format_version: int
    scan_idempotency_key: str
    started_at: str
    implementation_version: str
    contract_version: str
    observations: tuple[ObservationInput, ...]
    creation_authority: str = "HADocs"
    architecture_version: str = "DB-001"


@dataclass(frozen=True, slots=True)
class OperationalSliceResult:
    installation_id: int
    context_id: int
    audit_ids: tuple[int, int]
    scan_run_id: int
    observation_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class OperationalSliceRecords:
    installation: Mapping[str, object]
    context: Mapping[str, object]
    audits: tuple[Mapping[str, object], ...]
    scan_run: Mapping[str, object]
    observations: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class EntityPersistenceInput:
    entity_key: str
    raw_entity_id: str
    lifecycle_state: str = "ACTIVE"
    reason_code: str = ENTITY_PRESENT_REASON


@dataclass(frozen=True, slots=True)
class EntityPersistenceRequest:
    installation_id: int
    context_id: int
    scan_run_id: int
    observation_id: int
    event_at: str
    entities: tuple[EntityPersistenceInput, ...]
    authority: str = "HADocs"
    architecture_version: str = "DB-001"


@dataclass(frozen=True, slots=True)
class PersistedEntityResult:
    registration_id: int
    entity_id: int
    current_state_id: int
    lifecycle_event_id: int
    registration_audit_id: int
    lifecycle_audit_id: int
    opaque_reference: str
    lifecycle_state: str


@dataclass(frozen=True, slots=True)
class EntityPersistenceResult:
    installation_id: int
    context_id: int
    scan_run_id: int
    observation_id: int
    entities: tuple[PersistedEntityResult, ...]


@dataclass(frozen=True, slots=True)
class PersistedEntityRecords:
    registration: Mapping[str, object]
    entity: Mapping[str, object]
    current_state: Mapping[str, object]
    lifecycle_events: tuple[Mapping[str, object], ...]
    registration_audit: Mapping[str, object]
    lifecycle_audit: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class EntityPersistenceRecords:
    entities: tuple[PersistedEntityRecords, ...]


@dataclass(frozen=True, slots=True)
class RelationshipPersistenceInput:
    relationship_key: str
    raw_source_entity_id: str = field(repr=False)
    predicate: str
    target_kind: str
    raw_target_id: str = field(repr=False)
    current_status: str = "CURRENT"
    reason_code: str = RELATIONSHIP_PRESENT_REASON
    expected_target_ref: str | None = None


@dataclass(frozen=True, slots=True)
class RelationshipPersistenceRequest:
    installation_id: int
    context_id: int
    scan_run_id: int
    observation_id: int
    event_at: str
    relationships: tuple[RelationshipPersistenceInput, ...]
    authority: str = "HADocs"
    architecture_version: str = "DB-001"


@dataclass(frozen=True, slots=True)
class PersistedRelationshipResult:
    relationship_id: int
    current_state_id: int
    lifecycle_event_id: int
    lifecycle_audit_id: int
    target_registration_id: int | None
    target_registration_audit_id: int | None
    public_relationship_id: str
    predicate: str
    source_ref: str
    target_ref: str
    current_status: str


@dataclass(frozen=True, slots=True)
class RelationshipPersistenceResult:
    installation_id: int
    context_id: int
    scan_run_id: int
    observation_id: int
    relationships: tuple[PersistedRelationshipResult, ...]


@dataclass(frozen=True, slots=True)
class PersistedRelationshipRecords:
    relationship: Mapping[str, object]
    current_state: Mapping[str, object]
    lifecycle_events: tuple[Mapping[str, object], ...]
    lifecycle_audit: Mapping[str, object]
    audit_subject_links: tuple[Mapping[str, object], ...]
    audit_evidence_links: tuple[Mapping[str, object], ...]
    target_registration: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class RelationshipPersistenceRecords:
    relationships: tuple[PersistedRelationshipRecords, ...]


@dataclass(frozen=True, slots=True)
class CapabilityOutcomeInput:
    capability_id: str
    status: str
    retryable: bool | None
    safe_error_code: str | None
    observation_contribution: bool
    completeness_contribution: str


@dataclass(frozen=True, slots=True)
class ScanCompletionRequest:
    scan_run_id: int
    expected_installation_id: int
    completion_idempotency_key: str
    terminal_at: str
    terminal_status: str
    completeness: str
    safe_error_code: str | None
    capabilities: tuple[CapabilityOutcomeInput, ...]
    observation_ids: tuple[int, ...]
    authority: str = "HADocs"
    architecture_version: str = "DB-001"


@dataclass(frozen=True, slots=True)
class ScanCompletionResult:
    scan_run_id: int
    terminal_status: str
    completeness: str
    terminal_at: str
    safe_error_code: str | None
    capability_outcome_ids: tuple[int, ...]
    audit_id: int
    observation_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ScanCompletionRecords:
    scan_run: Mapping[str, object]
    capability_outcomes: tuple[Mapping[str, object], ...]
    audit: Mapping[str, object]
    subject_links: tuple[Mapping[str, object], ...]
    evidence_links: tuple[Mapping[str, object], ...]
    observations: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class ScanCompletionIntent:
    """Terminal caller intent without database-generated persistence identities."""

    completion_idempotency_key: str
    terminal_at: str
    terminal_status: str
    completeness: str
    safe_error_code: str | None
    capabilities: tuple[CapabilityOutcomeInput, ...]
    authority: str = "HADocs"
    architecture_version: str = "DB-001"

    def bind(
        self,
        operational_slice: OperationalSliceResult,
        *,
        observation_ids: tuple[int, ...] | None = None,
    ) -> ScanCompletionRequest:
        """Bind semantic intent to persisted IDs returned by the start operation."""

        return ScanCompletionRequest(
            scan_run_id=operational_slice.scan_run_id,
            expected_installation_id=operational_slice.installation_id,
            completion_idempotency_key=self.completion_idempotency_key,
            terminal_at=self.terminal_at,
            terminal_status=self.terminal_status,
            completeness=self.completeness,
            safe_error_code=self.safe_error_code,
            capabilities=self.capabilities,
            observation_ids=(
                operational_slice.observation_ids
                if observation_ids is None
                else observation_ids
            ),
            authority=self.authority,
            architecture_version=self.architecture_version,
        )


class OperationalReplayState(str, Enum):
    NEW_RUNNING = "new_running"
    EXISTING_RUNNING = "existing_running"
    EXISTING_TERMINAL = "existing_terminal"


@dataclass(frozen=True, slots=True)
class OperationalReplayResult:
    """Explicit result of starting or read-only replaying one scan operation."""

    state: OperationalReplayState
    operational_slice: OperationalSliceResult
    completion: ScanCompletionResult | None

    def __post_init__(self) -> None:
        is_terminal = self.state is OperationalReplayState.EXISTING_TERMINAL
        if is_terminal != (self.completion is not None):
            raise ValueError("terminal replay state and completion result must agree")


@dataclass(frozen=True, slots=True)
class _NormalizedObservation:
    source: ObservationInput
    payload_json: str
    immutable_digest: bytes


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationFailureError(f"{name} must be non-empty text")


def _semantic_match(
    record: Mapping[str, object],
    expected: Mapping[str, object],
    identity: str,
) -> None:
    if any(record.get(name) != value for name, value in expected.items()):
        raise IdempotencyConflictError(
            f"{identity} has conflicting semantic intent for its idempotency identity"
        )


def _ca001_frame(value: str) -> bytes:
    encoded = unicodedata.normalize("NFC", value).encode("utf-8", errors="strict")
    if not encoded or len(encoded) > 0xFFFFFFFF:
        raise ValidationFailureError("CA-001 text component is invalid")
    return struct.pack(">I", len(encoded)) + encoded


def _derive_ca001_reference(
    secret: bytes,
    installation_scope: str,
    reference_kind: str,
    raw_identifier: str,
) -> tuple[str, str, bytes]:
    if not isinstance(secret, bytes) or len(secret) != 32:
        from .errors import SecretUnavailableError

        raise SecretUnavailableError("protected identity secret is malformed")
    if not _CA001_SCOPE_PATTERN.fullmatch(installation_scope):
        raise ValidationFailureError("operational installation scope is invalid")
    if reference_kind not in _CA001_REFERENCE_KINDS:
        raise ValidationFailureError("CA-001 reference kind is not supported")
    normalized = unicodedata.normalize("NFC", raw_identifier)
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise ValidationFailureError("CA-001 raw identifier is invalid")
    message = (
        _CA001_DOMAIN
        + struct.pack(">I", 1)
        + struct.pack(">I", 3)
        + _ca001_frame(reference_kind)
        + _ca001_frame(installation_scope)
        + _ca001_frame(normalized)
    )
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    digest_hex = digest.hex()
    return f"refh1_{reference_kind}_{digest_hex}", digest_hex, digest


def _derive_ca001_entity(
    secret: bytes, installation_scope: str, raw_entity_id: str
) -> tuple[str, str, bytes]:
    return _derive_ca001_reference(
        secret, installation_scope, "entity", raw_entity_id
    )


def _loaded_component_canonical_key(raw_component: str) -> str:
    normalized = unicodedata.normalize("NFC", raw_component)
    if not normalized or any(
        ord(character) < 32 or ord(character) == 127
        for character in normalized
    ):
        raise ValidationFailureError("loaded-component identity input is invalid")
    try:
        encoded = normalized.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ValidationFailureError(
            "loaded-component identity input is invalid"
        ) from error
    unreserved = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    component = "".join(
        chr(byte) if byte in unreserved else f"%{byte:02X}" for byte in encoded
    )
    return f"ck1:loaded_component:{component}"


def _derive_loaded_component_reference(
    installation_scope: str, raw_component: str
) -> str:
    if not _CA001_SCOPE_PATTERN.fullmatch(installation_scope):
        raise ValidationFailureError("operational installation scope is invalid")
    canonical_key = _loaded_component_canonical_key(raw_component)
    payload = (
        _ca001_frame("hadocs-generic-metadata/observation-id/v1")
        + _ca001_frame(installation_scope)
        + _ca001_frame("rest.components")
        + _ca001_frame(canonical_key)
    )
    return f"obs1_{hashlib.sha256(payload).hexdigest()}"


def _derive_relationship_reference(
    installation_scope: str,
    predicate: str,
    source_ref: str,
    target_ref: str,
) -> str:
    if not _CA001_SCOPE_PATTERN.fullmatch(installation_scope):
        raise ValidationFailureError("operational installation scope is invalid")
    payload = (
        _ca001_frame("hadocs-generic-metadata/relationship-id/v1")
        + _ca001_frame(installation_scope)
        + _ca001_frame(predicate)
        + _ca001_frame(source_ref)
        + _ca001_frame(target_ref)
    )
    return f"rel1_{hashlib.sha256(payload).hexdigest()}"


class HaskDatabaseService:
    """Default-disabled operational database boundary."""

    def __init__(
        self,
        factory: HaskSQLiteConnectionFactory,
        secret_provider: SecretProvider | None = None,
        *,
        clock: Callable[[], str] = _utc_now,
        require_protected_identity: bool = False,
    ) -> None:
        self.factory = factory
        self.secret_provider = secret_provider or NullSecretProvider()
        self._clock = clock
        self._require_protected_identity = require_protected_identity
        self._managed: ManagedSQLiteConnection | None = None
        self._transactions: SerializedTransactionManager | None = None

    def startup(self) -> ServiceStatus:
        if not self.factory.config.enabled:
            return ServiceStatus(ServiceState.DISABLED)
        if self._require_protected_identity and isinstance(
            self.secret_provider, NullSecretProvider
        ):
            from .errors import SecretUnavailableError

            raise SecretUnavailableError(
                "enabled operational persistence requires a protected secret provider"
            )
        if self._managed is not None:
            return ServiceStatus(ServiceState.ACTIVE)
        managed = self.factory.open_for_migration(CURRENT_SCHEMA_VERSION)
        try:
            version = initialize_batch2_schema(managed.connection)
            if version != CURRENT_SCHEMA_VERSION:
                raise HaskDatabaseError(
                    f"database migration stopped at unsupported schema version {version}"
                )
            verify_schema(managed.connection)
            transactions = SerializedTransactionManager(managed.connection)
        except Exception:
            managed.close(verify=False)
            raise
        self._managed = managed
        self._transactions = transactions
        return ServiceStatus(ServiceState.ACTIVE)

    def shutdown(self) -> ServiceStatus:
        if self._managed is not None:
            self._managed.close()
            self._managed = None
            self._transactions = None
        return ServiceStatus(ServiceState.STOPPED)

    def validate_operational_identity(self, request: OperationalSliceRequest) -> None:
        """Fail closed before a product scan can create or replace a context."""

        from .errors import RecoveryModeError, SecretUnavailableError

        if not self._require_protected_identity:
            return
        if not _CA001_SCOPE_PATTERN.fullmatch(request.installation_scope):
            raise SecretUnavailableError("operational installation scope is invalid")
        if (
            request.secret_handle == "hadocs:no-secret:v1"
            or "no-secret" in request.secret_handle.lower()
        ):
            raise SecretUnavailableError("placeholder database identity is prohibited")
        secret = self.secret_provider.load(
            request.secret_handle, request.secret_generation
        )
        if not isinstance(secret, bytes) or len(secret) != 32:
            raise SecretUnavailableError(
                "protected identity secret is malformed"
            )

        installations, _, _, _ = self._read_repositories()
        installation = installations.get_by_recovery_set_ref(
            request.recovery_set_ref
        )
        if installation is None:
            return
        current_context_id = installation.get("current_context_id")
        if current_context_id is None:
            raise RecoveryModeError(
                "existing operational installation has no active identity context"
            )
        context = installations.get_context(int(current_context_id))
        if context is None:
            raise RecoveryModeError(
                "existing operational identity context is unavailable"
            )
        existing_scope = str(context["installation_scope"])
        existing_handle = str(context["secret_handle"])
        if (
            not _CA001_SCOPE_PATTERN.fullmatch(existing_scope)
            or existing_handle == "hadocs:no-secret:v1"
            or "no-secret" in existing_handle.lower()
        ):
            raise RecoveryModeError(
                "legacy placeholder database context requires explicit recovery"
            )
        expected = {
            "installation_scope": request.installation_scope,
            "secret_handle": request.secret_handle,
            "secret_generation": request.secret_generation,
            "format_version": request.context_format_version,
            "status": "ACTIVE",
        }
        if any(context.get(name) != value for name, value in expected.items()):
            raise RecoveryModeError(
                "existing operational database uses a different identity context"
            )

    def persist_operational_slice(
        self, request: OperationalSliceRequest
    ) -> OperationalSliceResult:
        normalized = self._normalize_request(request)
        transactions = self._require_transactions()
        persisted_at = self._clock()

        with transactions.unit_of_work() as unit:
            installations = cast(
                LogicalInstallationRepository,
                unit.repository(RepositoryOwner.LOGICAL_INSTALLATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )

            installation = installations.get_by_recovery_set_ref(request.recovery_set_ref)
            if installation is None:
                installation_id = installations.create_installation(
                    state="ACTIVE",
                    created_at=persisted_at,
                    creation_authority=request.creation_authority,
                    recovery_set_ref=request.recovery_set_ref,
                )
                installation = installations.get_installation(installation_id)
                assert installation is not None
            else:
                installation_id = int(installation["id"])
                _semantic_match(
                    installation,
                    {
                        "state": "ACTIVE",
                        "creation_authority": request.creation_authority,
                        "recovery_set_ref": request.recovery_set_ref,
                    },
                    "logical installation",
                )

            installation_audit_id = self._get_or_create_audit(
                audits,
                installation_id=installation_id,
                idempotency_key=self._audit_key(
                    "INSTALLATION_CREATED",
                    {"recovery_set_ref": request.recovery_set_ref},
                ),
                event_kind="INSTALLATION_CREATED",
                recorded_at=persisted_at,
                request=request,
            )
            context_audit_id = self._get_or_create_audit(
                audits,
                installation_id=installation_id,
                idempotency_key=self._audit_key(
                    "CONTEXT_ACTIVATED",
                    {
                        "recovery_set_ref": request.recovery_set_ref,
                        "installation_scope": request.installation_scope,
                        "secret_generation": request.secret_generation,
                        "format_version": request.context_format_version,
                    },
                ),
                event_kind="CONTEXT_ACTIVATED",
                recorded_at=persisted_at,
                request=request,
            )

            context = installations.get_context_by_identity(
                installation_id=installation_id,
                installation_scope=request.installation_scope,
                secret_generation=request.secret_generation,
                format_version=request.context_format_version,
            )
            if context is None:
                context_id = installations.create_context(
                    installation_id=installation_id,
                    installation_scope=request.installation_scope,
                    secret_handle=request.secret_handle,
                    secret_generation=request.secret_generation,
                    format_version=request.context_format_version,
                    valid_from=persisted_at,
                    activation_audit_id=context_audit_id,
                )
                context = installations.get_context(context_id)
                assert context is not None
            else:
                context_id = int(context["id"])
                _semantic_match(
                    context,
                    {
                        "installation_id": installation_id,
                        "installation_scope": request.installation_scope,
                        "secret_handle": request.secret_handle,
                        "secret_generation": request.secret_generation,
                        "format_version": request.context_format_version,
                        "status": "ACTIVE",
                        "activation_audit_id": context_audit_id,
                    },
                    "installation context",
                )

            current_context_id = installation.get("current_context_id")
            if current_context_id is None:
                installations.set_current_context(installation_id, context_id)
            elif int(current_context_id) != context_id:
                raise IdempotencyConflictError(
                    "logical installation has a different active context"
                )

            scan = scans.get_by_idempotency(
                installation_id, request.scan_idempotency_key
            )
            scan_existed = scan is not None
            if scan is None:
                scan_run_id = scans.create_running(
                    installation_id=installation_id,
                    context_id=context_id,
                    idempotency_key=request.scan_idempotency_key,
                    started_at=request.started_at,
                    implementation_version=request.implementation_version,
                    contract_version=request.contract_version,
                )
            else:
                scan_run_id = int(scan["id"])
                _semantic_match(
                    scan,
                    {
                        "installation_id": installation_id,
                        "context_id": context_id,
                        "idempotency_key": request.scan_idempotency_key,
                        "started_at": request.started_at,
                        "terminal_at": None,
                        "status": "RUNNING",
                        "completeness": "PENDING",
                        "safe_error_code": None,
                        "implementation_version": request.implementation_version,
                        "contract_version": request.contract_version,
                    },
                    "scan run",
                )

            existing_observations = observations.list_for_run(scan_run_id)
            if scan_existed:
                existing_keys = {str(item["observation_key"]) for item in existing_observations}
                requested_keys = {item.source.observation_key for item in normalized}
                if existing_keys != requested_keys:
                    raise IdempotencyConflictError(
                        "scan run has a conflicting structured observation set"
                    )

            observation_ids: list[int] = []
            for item in normalized:
                observation = observations.get_by_key(
                    scan_run_id, item.source.observation_key
                )
                if observation is None:
                    observation_id = observations.create(
                        scan_run_id=scan_run_id,
                        observation_key=item.source.observation_key,
                        taxonomy_class=item.source.taxonomy_class,
                        authority_class=item.source.authority_class,
                        provenance_ref=item.source.provenance_ref,
                        observed_at=item.source.observed_at,
                        normalized_payload_json=item.payload_json,
                        privacy_class=item.source.privacy_class,
                        retention_policy=item.source.retention_policy,
                        immutable_digest=item.immutable_digest,
                        created_at=persisted_at,
                    )
                else:
                    observation_id = int(observation["id"])
                    _semantic_match(
                        observation,
                        {
                            "scan_run_id": scan_run_id,
                            "observation_key": item.source.observation_key,
                            "taxonomy_class": item.source.taxonomy_class,
                            "authority_class": item.source.authority_class,
                            "provenance_ref": item.source.provenance_ref,
                            "observed_at": item.source.observed_at,
                            "normalized_payload_json": item.payload_json,
                            "privacy_class": item.source.privacy_class,
                            "retention_policy": item.source.retention_policy,
                            "immutable_digest": item.immutable_digest,
                        },
                        "observation",
                    )
                observation_ids.append(observation_id)

            return OperationalSliceResult(
                installation_id=installation_id,
                context_id=context_id,
                audit_ids=(installation_audit_id, context_audit_id),
                scan_run_id=scan_run_id,
                observation_ids=tuple(observation_ids),
            )

    def start_or_replay_operational_slice(
        self,
        request: OperationalSliceRequest,
        *,
        completion_intent: ScanCompletionIntent | None = None,
    ) -> OperationalReplayResult:
        """Start a new operation or resolve an equivalent persisted operation.

        Existing RUNNING and terminal operations are resolved through repository
        reads on the active autocommit connection.  Those replay paths issue no
        write transaction, INSERT, or UPDATE.  A terminal replay requires the
        caller's completion intent so every persisted terminal artifact can be
        compared before the original IDs are returned.
        """

        normalized = self._normalize_request(request)
        installations, audits, scans, observations = self._read_repositories()
        installation = installations.get_by_recovery_set_ref(
            request.recovery_set_ref
        )
        if installation is None:
            created = self.persist_operational_slice(request)
            return OperationalReplayResult(
                state=OperationalReplayState.NEW_RUNNING,
                operational_slice=created,
                completion=None,
            )

        installation_id = int(installation["id"])
        scan = scans.get_by_idempotency(
            installation_id, request.scan_idempotency_key
        )
        if scan is None:
            created = self.persist_operational_slice(request)
            return OperationalReplayResult(
                state=OperationalReplayState.NEW_RUNNING,
                operational_slice=created,
                completion=None,
            )

        start_result = self._validate_existing_operational_slice(
            request=request,
            normalized=normalized,
            installation=installation,
            scan=scan,
            installations=installations,
            audits=audits,
            observations=observations,
        )
        status = str(scan["status"])
        if status == "RUNNING":
            _semantic_match(
                scan,
                {
                    "terminal_at": None,
                    "status": "RUNNING",
                    "completeness": "PENDING",
                    "safe_error_code": None,
                },
                "scan run",
            )
            linked_terminal_audits = audits.list_for_subject(
                subject_kind="SCAN_RUN",
                subject_id=start_result.scan_run_id,
                role=SCAN_AUDIT_SUBJECT_ROLE,
            )
            audit_for_idempotency = (
                None
                if completion_intent is None
                else audits.get_by_idempotency(
                    start_result.installation_id,
                    completion_intent.completion_idempotency_key,
                )
            )
            validate_no_partial_completion(
                existing_capabilities=scans.list_capability_outcomes(
                    start_result.scan_run_id
                ),
                linked_terminal_audits=linked_terminal_audits,
                audit_for_idempotency=audit_for_idempotency,
            )
            return OperationalReplayResult(
                state=OperationalReplayState.EXISTING_RUNNING,
                operational_slice=start_result,
                completion=None,
            )

        if completion_intent is None:
            raise ValidationFailureError(
                "terminal replay requires explicit completion intent"
            )
        completion = self._validate_terminal_replay(
            start_result=start_result,
            scan=scan,
            intent=completion_intent,
            scans=scans,
            observations=observations,
            audits=audits,
        )
        return OperationalReplayResult(
            state=OperationalReplayState.EXISTING_TERMINAL,
            operational_slice=start_result,
            completion=completion,
        )

    def read_operational_slice(
        self, result: OperationalSliceResult
    ) -> OperationalSliceRecords:
        transactions = self._require_transactions()
        with transactions.unit_of_work() as unit:
            installations = cast(
                LogicalInstallationRepository,
                unit.repository(RepositoryOwner.LOGICAL_INSTALLATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )
            installation = installations.get_installation(result.installation_id)
            context = installations.get_context(result.context_id)
            scan_run = scans.get(result.scan_run_id)
            audit_rows = tuple(audits.get(item) for item in result.audit_ids)
            observation_rows = tuple(observations.get(item) for item in result.observation_ids)
            if (
                installation is None
                or context is None
                or scan_run is None
                or any(item is None for item in audit_rows)
                or any(item is None for item in observation_rows)
            ):
                raise NotFoundError("the operational slice is incomplete")
            return OperationalSliceRecords(
                installation=installation,
                context=context,
                audits=cast(tuple[Mapping[str, object], ...], audit_rows),
                scan_run=scan_run,
                observations=cast(tuple[Mapping[str, object], ...], observation_rows),
            )

    def persist_entities(
        self, request: EntityPersistenceRequest
    ) -> EntityPersistenceResult:
        for name in ("installation_id", "context_id", "scan_run_id", "observation_id"):
            value = getattr(request, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValidationFailureError("entity persistence IDs must be positive integers")
        _require_text(request.event_at, "event_at")
        _require_text(request.authority, "authority")
        _require_text(request.architecture_version, "architecture_version")
        if not request.entities:
            raise ValidationFailureError("entity persistence requires at least one entity")
        keys: set[str] = set()
        normalized_inputs: list[tuple[EntityPersistenceInput, str]] = []
        normalized_raws: set[str] = set()
        for item in request.entities:
            validate_entity_intent(
                entity_key=item.entity_key,
                raw_entity_id=item.raw_entity_id,
                lifecycle_state=item.lifecycle_state,
                reason_code=item.reason_code,
            )
            try:
                normalized_raw = unicodedata.normalize("NFC", item.raw_entity_id)
                normalized_raw.encode("utf-8", errors="strict")
            except (TypeError, UnicodeError) as error:
                raise ValidationFailureError(
                    "authoritative entity identity is invalid"
                ) from error
            if item.entity_key in keys:
                raise ValidationFailureError("entity intent keys must be unique")
            if normalized_raw in normalized_raws:
                raise ValidationFailureError("authoritative entity identities must be unique")
            keys.add(item.entity_key)
            normalized_raws.add(normalized_raw)
            normalized_inputs.append((item, normalized_raw))

        transactions = self._require_transactions()
        with transactions.unit_of_work(ENTITY_PERSISTENCE_CONTRACT) as unit:
            installations = cast(
                LogicalInstallationRepository,
                unit.repository(RepositoryOwner.LOGICAL_INSTALLATION),
            )
            registries = cast(
                CollisionRegistryRepository,
                unit.repository(RepositoryOwner.COLLISION_REGISTRY),
            )
            entities = cast(EntityRepository, unit.repository(RepositoryOwner.ENTITY))
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))

            installation = installations.get_installation(request.installation_id)
            context = installations.get_context(request.context_id)
            scan = scans.get(request.scan_run_id)
            observation = observations.get(request.observation_id)
            if installation is None or context is None or scan is None or observation is None:
                raise NotFoundError("entity persistence prerequisite is unavailable")
            if (
                installation.get("state") != "ACTIVE"
                or installation.get("current_context_id") != request.context_id
                or context.get("installation_id") != request.installation_id
                or context.get("status") != "ACTIVE"
            ):
                raise ValidationFailureError("entity persistence identity context is not active")
            if (
                scan.get("installation_id") != request.installation_id
                or scan.get("context_id") != request.context_id
                or scan.get("status") != "RUNNING"
                or observation.get("scan_run_id") != request.scan_run_id
            ):
                raise ValidationFailureError("entity persistence requires owned running-scan evidence")
            format_version = int(context["format_version"])
            secret_generation = int(context["secret_generation"])
            if format_version != 1:
                raise ValidationFailureError("entity persistence requires CA-001 format version 1")
            secret = self.secret_provider.load(
                str(context["secret_handle"]), secret_generation
            )

            registry = registries.get_registry_for_installation(request.installation_id)
            if registry is None:
                registry_id = registries.create_registry(
                    installation_id=request.installation_id,
                    format_version=format_version,
                    created_at=request.event_at,
                )
                registry = registries.get_registry_for_installation(
                    request.installation_id
                )
                assert registry is not None
            else:
                registry_id = int(registry["id"])
            _semantic_match(
                registry,
                {
                    "installation_id": request.installation_id,
                    "integrity_status": "VALID",
                    "availability_status": "AVAILABLE",
                    "format_version": format_version,
                },
                "collision registry",
            )

            results: list[PersistedEntityResult] = []
            for item, normalized_raw in normalized_inputs:
                opaque_reference, tuple_handle, identity_digest = _derive_ca001_entity(
                    secret, str(context["installation_scope"]), normalized_raw
                )
                by_tuple = registries.get_registration_by_tuple(
                    registry_id=registry_id,
                    context_id=request.context_id,
                    reference_kind="entity",
                    format_version=format_version,
                    canonical_tuple_handle=tuple_handle,
                    secret_generation=secret_generation,
                )
                by_reference = registries.get_registration_by_reference(
                    registry_id=registry_id,
                    context_id=request.context_id,
                    reference_kind="entity",
                    format_version=format_version,
                    opaque_reference=opaque_reference,
                )
                if (
                    by_tuple is not None
                    and by_reference is not None
                    and int(by_tuple["id"]) != int(by_reference["id"])
                ):
                    raise IdempotencyConflictError("protected entity identity collision detected")
                registration = by_tuple or by_reference
                registration_audit_key = self._audit_key(
                    "IDENTITY_REGISTERED", {"opaque_reference": opaque_reference}
                )
                registration_audit = audits.get_by_idempotency(
                    request.installation_id, registration_audit_key
                )
                if registration is None:
                    if registration_audit is not None:
                        raise IdempotencyConflictError(
                            "protected entity registration identity is already in use"
                        )
                    registration_audit_id = audits.create(
                        installation_id=request.installation_id,
                        idempotency_key=registration_audit_key,
                        event_kind="IDENTITY_REGISTERED",
                        recorded_at=request.event_at,
                        authority=request.authority,
                        provenance_ref=None,
                        architecture_version=request.architecture_version,
                        contract_version=str(scan["contract_version"]),
                        schema_version=CURRENT_SCHEMA_VERSION,
                        implementation_version=str(scan["implementation_version"]),
                        outcome="SUCCEEDED",
                        safe_failure_code=None,
                    )
                    registration_id = registries.create_registration(
                        registry_id=registry_id,
                        context_id=request.context_id,
                        reference_kind="entity",
                        format_version=format_version,
                        canonical_tuple_handle=tuple_handle,
                        opaque_reference=opaque_reference,
                        secret_generation=secret_generation,
                        registered_at=request.event_at,
                        registration_audit_id=registration_audit_id,
                        identity_digest=identity_digest,
                    )
                    audits.create_subject_link(
                        audit_id=registration_audit_id,
                        subject_kind="IDENTITY_REGISTRATION",
                        subject_id=registration_id,
                        role="REGISTERED_IDENTITY",
                    )
                    audits.create_evidence_link(
                        audit_id=registration_audit_id,
                        observation_id=request.observation_id,
                        role="REGISTRATION_EVIDENCE",
                        ordinal=0,
                    )
                    registration = registries.get_registration(registration_id)
                    assert registration is not None
                else:
                    registration_id = int(registration["id"])
                    _semantic_match(
                        registration,
                        {
                            "registry_id": registry_id,
                            "context_id": request.context_id,
                            "reference_kind": "entity",
                            "format_version": format_version,
                            "canonical_tuple_handle": tuple_handle,
                            "opaque_reference": opaque_reference,
                            "secret_generation": secret_generation,
                            "status": "ACTIVE",
                            "retired_at": None,
                            "identity_digest": identity_digest,
                        },
                        "protected entity registration",
                    )
                    registration_audit_id = int(registration["registration_audit_id"])
                    registration_audit = audits.get(registration_audit_id)
                    if registration_audit is None:
                        raise IdempotencyConflictError(
                            "protected entity registration audit is unavailable"
                        )

                entity = entities.get_by_registration(registration_id)
                if entity is None:
                    entity_id = entities.create(
                        installation_id=request.installation_id,
                        context_id=request.context_id,
                        identity_registration_id=registration_id,
                        created_at=request.event_at,
                    )
                    entity = entities.get(entity_id)
                    assert entity is not None
                else:
                    entity_id = int(entity["id"])
                    _semantic_match(
                        entity,
                        {
                            "installation_id": request.installation_id,
                            "context_id": request.context_id,
                            "identity_registration_id": registration_id,
                            "identity_status": "ACTIVE",
                        },
                        "entity",
                    )

                current = entities.get_current_state(entity_id)
                prior_state = None if current is None else str(current["lifecycle_state"])
                event_key = self._audit_key(
                    "ENTITY_TRANSITIONED",
                    {
                        "scan_idempotency_key": str(scan["idempotency_key"]),
                        "entity_key": item.entity_key,
                    },
                )
                existing_event = entities.get_event_by_idempotency(entity_id, event_key)
                lifecycle_audit = audits.get_by_idempotency(
                    request.installation_id, event_key
                )
                if existing_event is not None:
                    _semantic_match(
                        existing_event,
                        {
                            "entity_id": entity_id,
                            "idempotency_key": event_key,
                            "result_state": item.lifecycle_state,
                            "observation_id": request.observation_id,
                            "scan_run_id": request.scan_run_id,
                            "event_at": request.event_at,
                            "reason_code": item.reason_code,
                        },
                        "entity lifecycle event",
                    )
                    if lifecycle_audit is None or int(existing_event["audit_id"]) != int(
                        lifecycle_audit["id"]
                    ):
                        raise IdempotencyConflictError(
                            "entity lifecycle audit identity is inconsistent"
                        )
                    if current is None:
                        raise IdempotencyConflictError("entity current state is unavailable")
                    event_id = int(existing_event["id"])
                    lifecycle_audit_id = int(lifecycle_audit["id"])
                    current_state_id = int(current["id"])
                else:
                    requires_event = validate_entity_transition(
                        prior_state=prior_state,
                        result_state=item.lifecycle_state,
                        reason_code=item.reason_code,
                    )
                    if not requires_event:
                        assert current is not None
                        event_id = int(current["source_event_id"])
                        lifecycle_audit_id = int(current["audit_id"])
                        current_state_id = int(current["id"])
                    else:
                        if lifecycle_audit is not None:
                            raise IdempotencyConflictError(
                                "entity lifecycle intent identity is already in use"
                            )
                        lifecycle_audit_id = audits.create(
                            installation_id=request.installation_id,
                            idempotency_key=event_key,
                            event_kind="ENTITY_TRANSITIONED",
                            recorded_at=request.event_at,
                            authority=request.authority,
                            provenance_ref=None,
                            architecture_version=request.architecture_version,
                            contract_version=str(scan["contract_version"]),
                            schema_version=CURRENT_SCHEMA_VERSION,
                            implementation_version=str(scan["implementation_version"]),
                            outcome="SUCCEEDED",
                            safe_failure_code=None,
                        )
                        event_id = entities.create_event(
                            entity_id=entity_id,
                            idempotency_key=event_key,
                            prior_state=prior_state,
                            result_state=item.lifecycle_state,
                            observation_id=request.observation_id,
                            scan_run_id=request.scan_run_id,
                            audit_id=lifecycle_audit_id,
                            event_at=request.event_at,
                            reason_code=item.reason_code,
                        )
                        if current is None:
                            current_state_id = entities.create_current_state(
                                entity_id=entity_id,
                                lifecycle_state=item.lifecycle_state,
                                effective_at=request.event_at,
                                source_event_id=event_id,
                                scan_run_id=request.scan_run_id,
                                audit_id=lifecycle_audit_id,
                            )
                        else:
                            current_state_id = int(current["id"])
                            entities.transition_current_state(
                                entity_id=entity_id,
                                expected_state=prior_state,
                                expected_source_event_id=int(current["source_event_id"]),
                                lifecycle_state=item.lifecycle_state,
                                effective_at=request.event_at,
                                source_event_id=event_id,
                                scan_run_id=request.scan_run_id,
                                audit_id=lifecycle_audit_id,
                            )
                        audits.create_subject_link(
                            audit_id=lifecycle_audit_id,
                            subject_kind="ENTITY",
                            subject_id=entity_id,
                            role="LIFECYCLE_SUBJECT",
                        )
                        audits.create_evidence_link(
                            audit_id=lifecycle_audit_id,
                            observation_id=request.observation_id,
                            role="LIFECYCLE_EVIDENCE",
                            ordinal=0,
                        )
                results.append(PersistedEntityResult(
                    registration_id=registration_id,
                    entity_id=entity_id,
                    current_state_id=current_state_id,
                    lifecycle_event_id=event_id,
                    registration_audit_id=registration_audit_id,
                    lifecycle_audit_id=lifecycle_audit_id,
                    opaque_reference=opaque_reference,
                    lifecycle_state=item.lifecycle_state,
                ))
            return EntityPersistenceResult(
                installation_id=request.installation_id,
                context_id=request.context_id,
                scan_run_id=request.scan_run_id,
                observation_id=request.observation_id,
                entities=tuple(results),
            )

    def read_entities(
        self, result: EntityPersistenceResult
    ) -> EntityPersistenceRecords:
        transactions = self._require_transactions()
        with transactions.unit_of_work(ENTITY_PERSISTENCE_CONTRACT) as unit:
            registries = cast(
                CollisionRegistryRepository,
                unit.repository(RepositoryOwner.COLLISION_REGISTRY),
            )
            entities = cast(EntityRepository, unit.repository(RepositoryOwner.ENTITY))
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))
            records: list[PersistedEntityRecords] = []
            for item in result.entities:
                registration = registries.get_registration(item.registration_id)
                entity = entities.get(item.entity_id)
                current = entities.get_current_state(item.entity_id)
                registration_audit = audits.get(item.registration_audit_id)
                lifecycle_audit = audits.get(item.lifecycle_audit_id)
                if any(value is None for value in (
                    registration, entity, current, registration_audit, lifecycle_audit
                )):
                    raise NotFoundError("the persisted entity result is incomplete")
                records.append(PersistedEntityRecords(
                    registration=cast(Mapping[str, object], registration),
                    entity=cast(Mapping[str, object], entity),
                    current_state=cast(Mapping[str, object], current),
                    lifecycle_events=entities.list_events(item.entity_id),
                    registration_audit=cast(Mapping[str, object], registration_audit),
                    lifecycle_audit=cast(Mapping[str, object], lifecycle_audit),
                ))
            return EntityPersistenceRecords(tuple(records))

    def list_entities_for_installation(
        self, installation_id: int
    ) -> tuple[Mapping[str, object], ...]:
        if not isinstance(installation_id, int) or isinstance(installation_id, bool) or installation_id <= 0:
            raise ValidationFailureError("installation_id must be a positive integer")
        transactions = self._require_transactions()
        with transactions.unit_of_work(ENTITY_PERSISTENCE_CONTRACT) as unit:
            repository = cast(EntityRepository, unit.repository(RepositoryOwner.ENTITY))
            return repository.list_for_installation(installation_id)

    def persist_relationships(
        self, request: RelationshipPersistenceRequest
    ) -> RelationshipPersistenceResult:
        for name in ("installation_id", "context_id", "scan_run_id", "observation_id"):
            value = getattr(request, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValidationFailureError(
                    "relationship persistence IDs must be positive integers"
                )
        _require_text(request.event_at, "event_at")
        _require_text(request.authority, "authority")
        _require_text(request.architecture_version, "architecture_version")
        if not request.relationships:
            raise ValidationFailureError(
                "relationship persistence requires at least one relationship"
            )

        normalized_inputs: list[tuple[RelationshipPersistenceInput, str, str]] = []
        keys: set[str] = set()
        for item in request.relationships:
            validate_relationship_intent(
                relationship_key=item.relationship_key,
                raw_source_entity_id=item.raw_source_entity_id,
                predicate=item.predicate,
                target_kind=item.target_kind,
                raw_target_id=item.raw_target_id,
                current_status=item.current_status,
                reason_code=item.reason_code,
            )
            try:
                normalized_source = unicodedata.normalize(
                    "NFC", item.raw_source_entity_id
                )
                normalized_target = unicodedata.normalize("NFC", item.raw_target_id)
                normalized_source.encode("utf-8", errors="strict")
                normalized_target.encode("utf-8", errors="strict")
            except (TypeError, UnicodeError) as error:
                raise ValidationFailureError(
                    "relationship endpoint identity input is invalid"
                ) from error
            if item.relationship_key in keys:
                raise ValidationFailureError(
                    "relationship intent keys must be unique"
                )
            keys.add(item.relationship_key)
            if item.expected_target_ref is not None:
                if item.target_kind == "integration":
                    valid_expected = bool(
                        _OBSERVATION_REFERENCE_PATTERN.fullmatch(
                            item.expected_target_ref
                        )
                    )
                else:
                    valid_expected = bool(
                        _PROTECTED_REFERENCE_PATTERN.fullmatch(
                            item.expected_target_ref
                        )
                        and item.expected_target_ref.startswith(
                            f"refh1_{item.target_kind}_"
                        )
                    )
                if not valid_expected:
                    raise ValidationFailureError(
                        "protected relationship target reference is malformed"
                    )
            normalized_inputs.append((item, normalized_source, normalized_target))

        transactions = self._require_transactions()
        with transactions.unit_of_work(RELATIONSHIP_PERSISTENCE_CONTRACT) as unit:
            installations = cast(
                LogicalInstallationRepository,
                unit.repository(RepositoryOwner.LOGICAL_INSTALLATION),
            )
            registries = cast(
                CollisionRegistryRepository,
                unit.repository(RepositoryOwner.COLLISION_REGISTRY),
            )
            entities = cast(EntityRepository, unit.repository(RepositoryOwner.ENTITY))
            relationships = cast(
                RelationshipRepository,
                unit.repository(RepositoryOwner.RELATIONSHIP),
            )
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))

            installation = installations.get_installation(request.installation_id)
            context = installations.get_context(request.context_id)
            scan = scans.get(request.scan_run_id)
            observation = observations.get(request.observation_id)
            if installation is None or context is None or scan is None or observation is None:
                raise NotFoundError("relationship persistence prerequisite is unavailable")
            if (
                installation.get("state") != "ACTIVE"
                or installation.get("current_context_id") != request.context_id
                or context.get("installation_id") != request.installation_id
                or context.get("status") != "ACTIVE"
            ):
                raise ValidationFailureError(
                    "relationship persistence identity context is not active"
                )
            if (
                scan.get("installation_id") != request.installation_id
                or scan.get("context_id") != request.context_id
                or scan.get("status") != "RUNNING"
                or observation.get("scan_run_id") != request.scan_run_id
            ):
                raise ValidationFailureError(
                    "relationship persistence requires owned running-scan evidence"
                )
            format_version = int(context["format_version"])
            secret_generation = int(context["secret_generation"])
            if format_version != 1:
                raise ValidationFailureError(
                    "relationship persistence requires identity format version 1"
                )
            installation_scope = str(context["installation_scope"])
            secret = self.secret_provider.load(
                str(context["secret_handle"]), secret_generation
            )
            registry = registries.get_registry_for_installation(request.installation_id)
            if registry is None:
                raise NotFoundError(
                    "relationship source identity registry is unavailable"
                )
            registry_id = int(registry["id"])
            _semantic_match(
                registry,
                {
                    "installation_id": request.installation_id,
                    "integrity_status": "VALID",
                    "availability_status": "AVAILABLE",
                    "format_version": format_version,
                },
                "collision registry",
            )

            results: list[PersistedRelationshipResult] = []
            for item, normalized_source, normalized_target in normalized_inputs:
                source_ref, source_handle, _ = _derive_ca001_entity(
                    secret, installation_scope, normalized_source
                )
                source_registration = registries.get_registration_by_tuple(
                    registry_id=registry_id,
                    context_id=request.context_id,
                    reference_kind="entity",
                    format_version=format_version,
                    canonical_tuple_handle=source_handle,
                    secret_generation=secret_generation,
                )
                source_by_reference = registries.get_registration_by_reference(
                    registry_id=registry_id,
                    context_id=request.context_id,
                    reference_kind="entity",
                    format_version=format_version,
                    opaque_reference=source_ref,
                )
                if source_registration is None or source_by_reference is None:
                    raise NotFoundError(
                        "relationship source entity is not persisted"
                    )
                if int(source_registration["id"]) != int(source_by_reference["id"]):
                    raise IdempotencyConflictError(
                        "relationship source identity is inconsistent"
                    )
                source_entity = entities.get_by_registration(
                    int(source_registration["id"])
                )
                if source_entity is None:
                    raise NotFoundError(
                        "relationship source entity is not persisted"
                    )
                source_entity_id = int(source_entity["id"])
                _semantic_match(
                    source_entity,
                    {
                        "installation_id": request.installation_id,
                        "context_id": request.context_id,
                        "identity_registration_id": int(source_registration["id"]),
                        "identity_status": "ACTIVE",
                    },
                    "relationship source entity",
                )
                source_current = entities.get_current_state(source_entity_id)
                if source_current is None or (
                    item.current_status == "CURRENT"
                    and source_current.get("lifecycle_state") != "ACTIVE"
                ):
                    raise ValidationFailureError(
                        "relationship source entity is not currently eligible"
                    )

                target_registration_id: int | None = None
                target_registration_audit_id: int | None = None
                if item.target_kind == "integration":
                    target_ref = _derive_loaded_component_reference(
                        installation_scope, normalized_target
                    )
                else:
                    target_ref, target_handle, target_digest = _derive_ca001_reference(
                        secret,
                        installation_scope,
                        item.target_kind,
                        normalized_target,
                    )
                    target_by_tuple = registries.get_registration_by_tuple(
                        registry_id=registry_id,
                        context_id=request.context_id,
                        reference_kind=item.target_kind,
                        format_version=format_version,
                        canonical_tuple_handle=target_handle,
                        secret_generation=secret_generation,
                    )
                    target_by_reference = registries.get_registration_by_reference(
                        registry_id=registry_id,
                        context_id=request.context_id,
                        reference_kind=item.target_kind,
                        format_version=format_version,
                        opaque_reference=target_ref,
                    )
                    if (
                        target_by_tuple is not None
                        and target_by_reference is not None
                        and int(target_by_tuple["id"]) != int(target_by_reference["id"])
                    ):
                        raise IdempotencyConflictError(
                            "protected relationship target identity collision detected"
                        )
                    target_registration = target_by_tuple or target_by_reference
                    target_audit_key = self._audit_key(
                        "IDENTITY_REGISTERED", {"opaque_reference": target_ref}
                    )
                    target_audit = audits.get_by_idempotency(
                        request.installation_id, target_audit_key
                    )
                    if target_registration is None:
                        if target_audit is not None:
                            raise IdempotencyConflictError(
                                "protected target registration identity is already in use"
                            )
                        target_registration_audit_id = audits.create(
                            installation_id=request.installation_id,
                            idempotency_key=target_audit_key,
                            event_kind="IDENTITY_REGISTERED",
                            recorded_at=request.event_at,
                            authority=request.authority,
                            provenance_ref=None,
                            architecture_version=request.architecture_version,
                            contract_version=str(scan["contract_version"]),
                            schema_version=CURRENT_SCHEMA_VERSION,
                            implementation_version=str(scan["implementation_version"]),
                            outcome="SUCCEEDED",
                            safe_failure_code=None,
                        )
                        target_registration_id = registries.create_registration(
                            registry_id=registry_id,
                            context_id=request.context_id,
                            reference_kind=item.target_kind,
                            format_version=format_version,
                            canonical_tuple_handle=target_handle,
                            opaque_reference=target_ref,
                            secret_generation=secret_generation,
                            registered_at=request.event_at,
                            registration_audit_id=target_registration_audit_id,
                            identity_digest=target_digest,
                        )
                        audits.create_subject_link(
                            audit_id=target_registration_audit_id,
                            subject_kind="IDENTITY_REGISTRATION",
                            subject_id=target_registration_id,
                            role="REGISTERED_IDENTITY",
                        )
                        audits.create_evidence_link(
                            audit_id=target_registration_audit_id,
                            observation_id=request.observation_id,
                            role="REGISTRATION_EVIDENCE",
                            ordinal=0,
                        )
                    else:
                        target_registration_id = int(target_registration["id"])
                        _semantic_match(
                            target_registration,
                            {
                                "registry_id": registry_id,
                                "context_id": request.context_id,
                                "reference_kind": item.target_kind,
                                "format_version": format_version,
                                "canonical_tuple_handle": target_handle,
                                "opaque_reference": target_ref,
                                "secret_generation": secret_generation,
                                "status": "ACTIVE",
                                "retired_at": None,
                                "identity_digest": target_digest,
                            },
                            "protected relationship target registration",
                        )
                        target_registration_audit_id = int(
                            target_registration["registration_audit_id"]
                        )
                        if (
                            target_audit is None
                            or int(target_audit["id"])
                            != target_registration_audit_id
                        ):
                            raise IdempotencyConflictError(
                                "protected target registration audit is unavailable"
                            )

                if item.expected_target_ref is not None and (
                    item.expected_target_ref != target_ref
                ):
                    raise IdempotencyConflictError(
                        "protected relationship target reference conflicts with intent"
                    )
                if item.target_kind == "integration":
                    if not _OBSERVATION_REFERENCE_PATTERN.fullmatch(target_ref):
                        raise ValidationFailureError(
                            "protected relationship target reference is invalid"
                        )
                elif not (
                    _PROTECTED_REFERENCE_PATTERN.fullmatch(target_ref)
                    and target_ref.startswith(f"refh1_{item.target_kind}_")
                ):
                    raise ValidationFailureError(
                        "protected relationship target reference is invalid"
                    )

                public_relationship_id = _derive_relationship_reference(
                    installation_scope, item.predicate, source_ref, target_ref
                )
                if not _RELATIONSHIP_REFERENCE_PATTERN.fullmatch(
                    public_relationship_id
                ):
                    raise ValidationFailureError(
                        "protected relationship identity is invalid"
                    )
                by_tuple = relationships.get_by_tuple(
                    installation_id=request.installation_id,
                    predicate=item.predicate,
                    source_ref=source_ref,
                    target_ref=target_ref,
                )
                by_public = relationships.get_by_public_id(
                    request.installation_id, public_relationship_id
                )
                if (
                    by_tuple is not None
                    and by_public is not None
                    and int(by_tuple["id"]) != int(by_public["id"])
                ):
                    raise IdempotencyConflictError(
                        "protected relationship identity collision detected"
                    )
                relationship = by_tuple or by_public
                if relationship is None:
                    relationship_id = relationships.create(
                        installation_id=request.installation_id,
                        public_relationship_id=public_relationship_id,
                        predicate=item.predicate,
                        source_entity_id=source_entity_id,
                        source_ref=source_ref,
                        target_ref=target_ref,
                        created_at=request.event_at,
                    )
                    relationship = relationships.get(relationship_id)
                    assert relationship is not None
                else:
                    relationship_id = int(relationship["id"])
                    _semantic_match(
                        relationship,
                        {
                            "installation_id": request.installation_id,
                            "public_relationship_id": public_relationship_id,
                            "predicate": item.predicate,
                            "source_entity_id": source_entity_id,
                            "source_ref": source_ref,
                            "target_ref": target_ref,
                            "identity_status": "ACTIVE",
                        },
                        "relationship",
                    )

                current = relationships.get_current_state(relationship_id)
                event_key = self._audit_key(
                    "RELATIONSHIP_TRANSITIONED",
                    {
                        "scan_idempotency_key": str(scan["idempotency_key"]),
                        "relationship_key": item.relationship_key,
                    },
                )
                existing_event = relationships.get_event_by_idempotency(
                    relationship_id, event_key
                )
                lifecycle_audit = audits.get_by_idempotency(
                    request.installation_id, event_key
                )
                if existing_event is not None:
                    expected_event_kind = {
                        RELATIONSHIP_PRESENT_REASON: "CREATED",
                        RELATIONSHIP_REMOVAL_REASON: "REMOVED",
                        RELATIONSHIP_RECREATION_REASON: "RECREATED",
                    }[item.reason_code]
                    expected_event = {
                        "relationship_id": relationship_id,
                        "idempotency_key": event_key,
                        "event_kind": expected_event_kind,
                        "continuity": "PRESERVED",
                        "observation_id": request.observation_id,
                        "scan_run_id": request.scan_run_id,
                        "event_at": request.event_at,
                    }
                    if item.current_status == "CURRENT":
                        expected_event.update({
                            "result_predicate": item.predicate,
                            "result_source_ref": source_ref,
                            "result_target_ref": target_ref,
                        })
                    else:
                        expected_event.update({
                            "prior_predicate": item.predicate,
                            "prior_source_ref": source_ref,
                            "prior_target_ref": target_ref,
                            "result_predicate": None,
                            "result_source_ref": None,
                            "result_target_ref": None,
                        })
                    _semantic_match(
                        existing_event,
                        expected_event,
                        "relationship lifecycle event",
                    )
                    if (
                        lifecycle_audit is None
                        or int(existing_event["audit_id"])
                        != int(lifecycle_audit["id"])
                        or current is None
                        or int(current["source_event_id"])
                        != int(existing_event["id"])
                    ):
                        raise IdempotencyConflictError(
                            "relationship lifecycle replay is incomplete"
                        )
                    event_id = int(existing_event["id"])
                    lifecycle_audit_id = int(lifecycle_audit["id"])
                    current_state_id = int(current["id"])
                else:
                    prior_status = None if current is None else str(current["status"])
                    event_kind = validate_relationship_transition(
                        prior_status=prior_status,
                        result_status=item.current_status,
                        reason_code=item.reason_code,
                    )
                    if event_kind is None:
                        assert current is not None
                        expected_current = {
                            "status": item.current_status,
                            "predicate": (
                                item.predicate
                                if item.current_status == "CURRENT"
                                else None
                            ),
                            "source_ref": (
                                source_ref if item.current_status == "CURRENT" else None
                            ),
                            "target_ref": (
                                target_ref if item.current_status == "CURRENT" else None
                            ),
                        }
                        _semantic_match(
                            current, expected_current, "relationship current state"
                        )
                        event_id = int(current["source_event_id"])
                        source_event = relationships.get_event(event_id)
                        if source_event is None:
                            raise IdempotencyConflictError(
                                "relationship current source event is unavailable"
                            )
                        lifecycle_audit_id = int(source_event["audit_id"])
                        current_state_id = int(current["id"])
                    else:
                        if lifecycle_audit is not None:
                            raise IdempotencyConflictError(
                                "relationship lifecycle intent identity is already in use"
                            )
                        lifecycle_audit_id = audits.create(
                            installation_id=request.installation_id,
                            idempotency_key=event_key,
                            event_kind="RELATIONSHIP_TRANSITIONED",
                            recorded_at=request.event_at,
                            authority=request.authority,
                            provenance_ref=None,
                            architecture_version=request.architecture_version,
                            contract_version=str(scan["contract_version"]),
                            schema_version=CURRENT_SCHEMA_VERSION,
                            implementation_version=str(scan["implementation_version"]),
                            outcome="SUCCEEDED",
                            safe_failure_code=None,
                        )
                        has_result = item.current_status == "CURRENT"
                        has_prior = event_kind == "REMOVED"
                        event_id = relationships.create_event(
                            relationship_id=relationship_id,
                            idempotency_key=event_key,
                            event_kind=event_kind,
                            prior_predicate=item.predicate if has_prior else None,
                            prior_source_ref=source_ref if has_prior else None,
                            prior_target_ref=target_ref if has_prior else None,
                            result_predicate=item.predicate if has_result else None,
                            result_source_ref=source_ref if has_result else None,
                            result_target_ref=target_ref if has_result else None,
                            continuity="PRESERVED",
                            observation_id=request.observation_id,
                            scan_run_id=request.scan_run_id,
                            audit_id=lifecycle_audit_id,
                            event_at=request.event_at,
                        )
                        if current is None:
                            current_state_id = relationships.create_current_state(
                                relationship_id=relationship_id,
                                status=item.current_status,
                                predicate=item.predicate if has_result else None,
                                source_ref=source_ref if has_result else None,
                                target_ref=target_ref if has_result else None,
                                effective_at=request.event_at,
                                source_event_id=event_id,
                                scan_run_id=request.scan_run_id,
                            )
                        else:
                            current_state_id = int(current["id"])
                            relationships.transition_current_state(
                                relationship_id=relationship_id,
                                expected_status=str(current["status"]),
                                expected_source_event_id=int(current["source_event_id"]),
                                status=item.current_status,
                                predicate=item.predicate if has_result else None,
                                source_ref=source_ref if has_result else None,
                                target_ref=target_ref if has_result else None,
                                effective_at=request.event_at,
                                source_event_id=event_id,
                                scan_run_id=request.scan_run_id,
                            )
                        audits.create_subject_link(
                            audit_id=lifecycle_audit_id,
                            subject_kind="RELATIONSHIP",
                            subject_id=relationship_id,
                            role="LIFECYCLE_SUBJECT",
                        )
                        audits.create_evidence_link(
                            audit_id=lifecycle_audit_id,
                            observation_id=request.observation_id,
                            role="LIFECYCLE_EVIDENCE",
                            ordinal=0,
                        )

                results.append(PersistedRelationshipResult(
                    relationship_id=relationship_id,
                    current_state_id=current_state_id,
                    lifecycle_event_id=event_id,
                    lifecycle_audit_id=lifecycle_audit_id,
                    target_registration_id=target_registration_id,
                    target_registration_audit_id=target_registration_audit_id,
                    public_relationship_id=public_relationship_id,
                    predicate=item.predicate,
                    source_ref=source_ref,
                    target_ref=target_ref,
                    current_status=item.current_status,
                ))
            return RelationshipPersistenceResult(
                installation_id=request.installation_id,
                context_id=request.context_id,
                scan_run_id=request.scan_run_id,
                observation_id=request.observation_id,
                relationships=tuple(results),
            )

    def read_relationships(
        self, result: RelationshipPersistenceResult
    ) -> RelationshipPersistenceRecords:
        transactions = self._require_transactions()
        with transactions.unit_of_work(RELATIONSHIP_PERSISTENCE_CONTRACT) as unit:
            registries = cast(
                CollisionRegistryRepository,
                unit.repository(RepositoryOwner.COLLISION_REGISTRY),
            )
            relationships = cast(
                RelationshipRepository,
                unit.repository(RepositoryOwner.RELATIONSHIP),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))
            records: list[PersistedRelationshipRecords] = []
            for item in result.relationships:
                relationship = relationships.get(item.relationship_id)
                current = relationships.get_current_state(item.relationship_id)
                lifecycle_audit = audits.get(item.lifecycle_audit_id)
                target_registration = (
                    None
                    if item.target_registration_id is None
                    else registries.get_registration(item.target_registration_id)
                )
                if (
                    relationship is None
                    or current is None
                    or lifecycle_audit is None
                    or (
                        item.target_registration_id is not None
                        and target_registration is None
                    )
                ):
                    raise NotFoundError(
                        "the persisted relationship result is incomplete"
                    )
                records.append(PersistedRelationshipRecords(
                    relationship=relationship,
                    current_state=current,
                    lifecycle_events=relationships.list_events(item.relationship_id),
                    lifecycle_audit=lifecycle_audit,
                    audit_subject_links=audits.list_subject_links(
                        item.lifecycle_audit_id
                    ),
                    audit_evidence_links=audits.list_evidence_links(
                        item.lifecycle_audit_id
                    ),
                    target_registration=target_registration,
                ))
            return RelationshipPersistenceRecords(tuple(records))

    def list_relationships_for_installation(
        self, installation_id: int
    ) -> tuple[Mapping[str, object], ...]:
        if (
            not isinstance(installation_id, int)
            or isinstance(installation_id, bool)
            or installation_id <= 0
        ):
            raise ValidationFailureError("installation_id must be a positive integer")
        transactions = self._require_transactions()
        with transactions.unit_of_work(RELATIONSHIP_PERSISTENCE_CONTRACT) as unit:
            repository = cast(
                RelationshipRepository,
                unit.repository(RepositoryOwner.RELATIONSHIP),
            )
            return repository.list_for_installation(installation_id)

    def list_relationships_for_scan(
        self, scan_run_id: int
    ) -> tuple[Mapping[str, object], ...]:
        if (
            not isinstance(scan_run_id, int)
            or isinstance(scan_run_id, bool)
            or scan_run_id <= 0
        ):
            raise ValidationFailureError("scan_run_id must be a positive integer")
        transactions = self._require_transactions()
        with transactions.unit_of_work(RELATIONSHIP_PERSISTENCE_CONTRACT) as unit:
            repository = cast(
                RelationshipRepository,
                unit.repository(RepositoryOwner.RELATIONSHIP),
            )
            return repository.list_for_scan(scan_run_id)

    def list_relationships_for_source_entity(
        self, source_entity_id: int
    ) -> tuple[Mapping[str, object], ...]:
        if (
            not isinstance(source_entity_id, int)
            or isinstance(source_entity_id, bool)
            or source_entity_id <= 0
        ):
            raise ValidationFailureError(
                "source_entity_id must be a positive integer"
            )
        transactions = self._require_transactions()
        with transactions.unit_of_work(RELATIONSHIP_PERSISTENCE_CONTRACT) as unit:
            repository = cast(
                RelationshipRepository,
                unit.repository(RepositoryOwner.RELATIONSHIP),
            )
            return repository.list_for_source_entity(source_entity_id)

    def complete_scan(self, request: ScanCompletionRequest) -> ScanCompletionResult:
        if (
            not isinstance(request.scan_run_id, int)
            or isinstance(request.scan_run_id, bool)
            or request.scan_run_id <= 0
            or not isinstance(request.expected_installation_id, int)
            or isinstance(request.expected_installation_id, bool)
            or request.expected_installation_id <= 0
        ):
            raise ValidationFailureError("scan and installation IDs must be positive integers")
        _require_text(request.authority, "authority")
        _require_text(request.architecture_version, "architecture_version")
        validate_completion_intent(
            completion_idempotency_key=request.completion_idempotency_key,
            terminal_at=request.terminal_at,
            terminal_status=request.terminal_status,
            completeness=request.completeness,
            safe_error_code=request.safe_error_code,
            capabilities=request.capabilities,
            observation_ids=request.observation_ids,
        )
        transactions = self._require_transactions()
        with transactions.unit_of_work(SCAN_COMPLETION_CONTRACT) as unit:
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))

            scan = scans.get(request.scan_run_id)
            if scan is None:
                raise NotFoundError("scan completion target does not exist")
            is_retry = validate_scan_state(
                scan,
                expected_installation_id=request.expected_installation_id,
                terminal_at=request.terminal_at,
                terminal_status=request.terminal_status,
                completeness=request.completeness,
                safe_error_code=request.safe_error_code,
            )
            all_scan_observations = observations.list_for_run(request.scan_run_id)
            requested_observations = tuple(
                observations.get(item) for item in request.observation_ids
            )
            validate_observation_ownership(
                scan_run_id=request.scan_run_id,
                all_scan_observations=all_scan_observations,
                requested_observations=requested_observations,
                requested_ids=request.observation_ids,
            )

            existing_capabilities = scans.list_capability_outcomes(request.scan_run_id)
            linked_terminal_audits = audits.list_for_subject(
                subject_kind="SCAN_RUN",
                subject_id=request.scan_run_id,
                role=SCAN_AUDIT_SUBJECT_ROLE,
            )
            audit_for_idempotency = audits.get_by_idempotency(
                request.expected_installation_id,
                request.completion_idempotency_key,
            )

            if is_retry:
                if len(linked_terminal_audits) == 1:
                    linked_audit_id = int(linked_terminal_audits[0]["id"])
                    subject_links = audits.list_subject_links(linked_audit_id)
                    evidence_links = audits.list_evidence_links(linked_audit_id)
                else:
                    subject_links = ()
                    evidence_links = ()
                capability_ids, audit_id = validate_retry_artifacts(
                    scan=scan,
                    completion_idempotency_key=request.completion_idempotency_key,
                    terminal_at=request.terminal_at,
                    authority=request.authority,
                    architecture_version=request.architecture_version,
                    capabilities=request.capabilities,
                    existing_capabilities=existing_capabilities,
                    linked_terminal_audits=linked_terminal_audits,
                    audit_for_idempotency=audit_for_idempotency,
                    subject_links=subject_links,
                    evidence_links=evidence_links,
                    observation_ids=request.observation_ids,
                    schema_version=CURRENT_SCHEMA_VERSION,
                )
                return self._completion_result(
                    request,
                    capability_outcome_ids=capability_ids,
                    audit_id=audit_id,
                )

            validate_no_partial_completion(
                existing_capabilities=existing_capabilities,
                linked_terminal_audits=linked_terminal_audits,
                audit_for_idempotency=audit_for_idempotency,
            )
            capability_ids = tuple(
                scans.create_capability_outcome(
                    scan_run_id=request.scan_run_id,
                    capability_id=item.capability_id,
                    status=item.status,
                    retryable=item.retryable,
                    safe_error_code=item.safe_error_code,
                    observation_contribution=item.observation_contribution,
                    completeness_contribution=item.completeness_contribution,
                    recorded_at=request.terminal_at,
                )
                for item in request.capabilities
            )
            audit_id = audits.create(
                installation_id=request.expected_installation_id,
                idempotency_key=request.completion_idempotency_key,
                event_kind="SCAN_TERMINATED",
                recorded_at=request.terminal_at,
                authority=request.authority,
                provenance_ref=None,
                architecture_version=request.architecture_version,
                contract_version=str(scan["contract_version"]),
                schema_version=CURRENT_SCHEMA_VERSION,
                implementation_version=str(scan["implementation_version"]),
                outcome="SUCCEEDED",
                safe_failure_code=None,
            )
            audits.create_subject_link(
                audit_id=audit_id,
                subject_kind="SCAN_RUN",
                subject_id=request.scan_run_id,
                role=SCAN_AUDIT_SUBJECT_ROLE,
            )
            for ordinal, observation_id in enumerate(request.observation_ids):
                audits.create_evidence_link(
                    audit_id=audit_id,
                    observation_id=observation_id,
                    role=SCAN_AUDIT_EVIDENCE_ROLE,
                    ordinal=ordinal,
                )
            scans.terminalize(
                scan_run_id=request.scan_run_id,
                terminal_at=request.terminal_at,
                status=request.terminal_status,
                completeness=request.completeness,
                safe_error_code=request.safe_error_code,
            )
            return self._completion_result(
                request,
                capability_outcome_ids=capability_ids,
                audit_id=audit_id,
            )

    def read_scan_completion(
        self, result: ScanCompletionResult
    ) -> ScanCompletionRecords:
        transactions = self._require_transactions()
        with transactions.unit_of_work(SCAN_COMPLETION_CONTRACT) as unit:
            scans = cast(ScanRunRepository, unit.repository(RepositoryOwner.SCAN_RUN))
            observations = cast(
                ObservationRepository,
                unit.repository(RepositoryOwner.OBSERVATION),
            )
            audits = cast(AuditRepository, unit.repository(RepositoryOwner.AUDIT))
            scan = scans.get(result.scan_run_id)
            capability_rows = tuple(
                scans.get_capability_outcome_by_id(item)
                for item in result.capability_outcome_ids
            )
            audit = audits.get(result.audit_id)
            observation_rows = tuple(
                observations.get(item) for item in result.observation_ids
            )
            if (
                scan is None
                or audit is None
                or any(item is None for item in capability_rows)
                or any(item is None for item in observation_rows)
            ):
                raise NotFoundError("the persisted scan completion result is incomplete")
            return ScanCompletionRecords(
                scan_run=scan,
                capability_outcomes=cast(
                    tuple[Mapping[str, object], ...], capability_rows
                ),
                audit=audit,
                subject_links=audits.list_subject_links(result.audit_id),
                evidence_links=audits.list_evidence_links(result.audit_id),
                observations=cast(
                    tuple[Mapping[str, object], ...], observation_rows
                ),
            )

    def _require_transactions(self) -> SerializedTransactionManager:
        if self._transactions is None:
            raise HaskDatabaseError("database service is not active")
        return self._transactions

    def _read_repositories(
        self,
    ) -> tuple[
        LogicalInstallationRepository,
        AuditRepository,
        ScanRunRepository,
        ObservationRepository,
    ]:
        if self._managed is None:
            raise HaskDatabaseError("database service is not active")
        connection = self._managed.connection
        return (
            LogicalInstallationRepository(connection),
            AuditRepository(connection),
            ScanRunRepository(connection),
            ObservationRepository(connection),
        )

    def _validate_existing_operational_slice(
        self,
        *,
        request: OperationalSliceRequest,
        normalized: tuple[_NormalizedObservation, ...],
        installation: Mapping[str, object],
        scan: Mapping[str, object],
        installations: LogicalInstallationRepository,
        audits: AuditRepository,
        observations: ObservationRepository,
    ) -> OperationalSliceResult:
        installation_id = int(installation["id"])
        _semantic_match(
            installation,
            {
                "state": "ACTIVE",
                "creation_authority": request.creation_authority,
                "recovery_set_ref": request.recovery_set_ref,
            },
            "logical installation",
        )
        context = installations.get_context_by_identity(
            installation_id=installation_id,
            installation_scope=request.installation_scope,
            secret_generation=request.secret_generation,
            format_version=request.context_format_version,
        )
        if context is None:
            raise IdempotencyConflictError(
                "installation context is missing for the persisted scan intent"
            )
        context_id = int(context["id"])
        _semantic_match(
            context,
            {
                "installation_id": installation_id,
                "installation_scope": request.installation_scope,
                "secret_handle": request.secret_handle,
                "secret_generation": request.secret_generation,
                "format_version": request.context_format_version,
                "status": "ACTIVE",
            },
            "installation context",
        )
        if installation.get("current_context_id") != context_id:
            raise IdempotencyConflictError(
                "logical installation has a different active context"
            )
        _semantic_match(
            scan,
            {
                "installation_id": installation_id,
                "context_id": context_id,
                "idempotency_key": request.scan_idempotency_key,
                "started_at": request.started_at,
                "implementation_version": request.implementation_version,
                "contract_version": request.contract_version,
            },
            "scan run",
        )

        installation_audit_key = self._audit_key(
            "INSTALLATION_CREATED",
            {"recovery_set_ref": request.recovery_set_ref},
        )
        context_audit_key = self._audit_key(
            "CONTEXT_ACTIVATED",
            {
                "recovery_set_ref": request.recovery_set_ref,
                "installation_scope": request.installation_scope,
                "secret_generation": request.secret_generation,
                "format_version": request.context_format_version,
            },
        )
        start_audits = (
            audits.get_by_idempotency(installation_id, installation_audit_key),
            audits.get_by_idempotency(installation_id, context_audit_key),
        )
        if any(item is None for item in start_audits):
            raise IdempotencyConflictError(
                "persisted operational slice is missing a required start audit"
            )
        for audit, key, kind in zip(
            start_audits,
            (installation_audit_key, context_audit_key),
            ("INSTALLATION_CREATED", "CONTEXT_ACTIVATED"),
            strict=True,
        ):
            assert audit is not None
            _semantic_match(
                audit,
                {
                    "installation_id": installation_id,
                    "idempotency_key": key,
                    "event_kind": kind,
                    "outcome": "SUCCEEDED",
                    "safe_failure_code": None,
                },
                "audit record",
            )
        if context.get("activation_audit_id") != int(start_audits[1]["id"]):
            raise IdempotencyConflictError(
                "installation context has a conflicting activation audit"
            )

        persisted_observations = observations.list_for_run(int(scan["id"]))
        by_key = {
            str(item["observation_key"]): item for item in persisted_observations
        }
        if set(by_key) != {item.source.observation_key for item in normalized}:
            raise IdempotencyConflictError(
                "scan run has a conflicting structured observation set"
            )
        for item in normalized:
            _semantic_match(
                by_key[item.source.observation_key],
                {
                    "scan_run_id": int(scan["id"]),
                    "observation_key": item.source.observation_key,
                    "taxonomy_class": item.source.taxonomy_class,
                    "authority_class": item.source.authority_class,
                    "provenance_ref": item.source.provenance_ref,
                    "observed_at": item.source.observed_at,
                    "normalized_payload_json": item.payload_json,
                    "privacy_class": item.source.privacy_class,
                    "retention_policy": item.source.retention_policy,
                    "immutable_digest": item.immutable_digest,
                },
                "observation",
            )
        return OperationalSliceResult(
            installation_id=installation_id,
            context_id=context_id,
            audit_ids=cast(
                tuple[int, int], tuple(int(item["id"]) for item in start_audits)
            ),
            scan_run_id=int(scan["id"]),
            observation_ids=tuple(
                int(item["id"])
                for item in sorted(
                    persisted_observations, key=lambda observation: int(observation["id"])
                )
            ),
        )

    def _validate_terminal_replay(
        self,
        *,
        start_result: OperationalSliceResult,
        scan: Mapping[str, object],
        intent: ScanCompletionIntent,
        scans: ScanRunRepository,
        observations: ObservationRepository,
        audits: AuditRepository,
    ) -> ScanCompletionResult:
        linked_terminal_audits = audits.list_for_subject(
            subject_kind="SCAN_RUN",
            subject_id=start_result.scan_run_id,
            role=SCAN_AUDIT_SUBJECT_ROLE,
        )
        evidence_links = (
            audits.list_evidence_links(int(linked_terminal_audits[0]["id"]))
            if len(linked_terminal_audits) == 1
            else ()
        )
        evidence_ids = tuple(int(item["observation_id"]) for item in evidence_links)
        completion_request = intent.bind(
            start_result,
            observation_ids=evidence_ids,
        )
        validate_completion_intent(
            completion_idempotency_key=completion_request.completion_idempotency_key,
            terminal_at=completion_request.terminal_at,
            terminal_status=completion_request.terminal_status,
            completeness=completion_request.completeness,
            safe_error_code=completion_request.safe_error_code,
            capabilities=completion_request.capabilities,
            observation_ids=completion_request.observation_ids,
        )
        if not validate_scan_state(
            scan,
            expected_installation_id=completion_request.expected_installation_id,
            terminal_at=completion_request.terminal_at,
            terminal_status=completion_request.terminal_status,
            completeness=completion_request.completeness,
            safe_error_code=completion_request.safe_error_code,
        ):
            raise ValidationFailureError("terminal replay resolved a non-terminal scan")
        all_observations = observations.list_for_run(start_result.scan_run_id)
        requested_observations = tuple(
            observations.get(item) for item in completion_request.observation_ids
        )
        validate_observation_ownership(
            scan_run_id=start_result.scan_run_id,
            all_scan_observations=all_observations,
            requested_observations=requested_observations,
            requested_ids=completion_request.observation_ids,
        )
        audit_for_idempotency = audits.get_by_idempotency(
            start_result.installation_id,
            completion_request.completion_idempotency_key,
        )
        subject_links = (
            audits.list_subject_links(int(linked_terminal_audits[0]["id"]))
            if len(linked_terminal_audits) == 1
            else ()
        )
        existing_capabilities = scans.list_capability_outcomes(
            start_result.scan_run_id
        )
        _, audit_id = validate_retry_artifacts(
            scan=scan,
            completion_idempotency_key=completion_request.completion_idempotency_key,
            terminal_at=completion_request.terminal_at,
            authority=completion_request.authority,
            architecture_version=completion_request.architecture_version,
            capabilities=completion_request.capabilities,
            existing_capabilities=existing_capabilities,
            linked_terminal_audits=linked_terminal_audits,
            audit_for_idempotency=audit_for_idempotency,
            subject_links=subject_links,
            evidence_links=evidence_links,
            observation_ids=completion_request.observation_ids,
            schema_version=CURRENT_SCHEMA_VERSION,
        )
        return self._completion_result(
            completion_request,
            capability_outcome_ids=tuple(
                int(item["id"])
                for item in sorted(
                    existing_capabilities,
                    key=lambda capability: int(capability["id"]),
                )
            ),
            audit_id=audit_id,
        )

    def _normalize_request(
        self, request: OperationalSliceRequest
    ) -> tuple[_NormalizedObservation, ...]:
        for name in (
            "recovery_set_ref",
            "installation_scope",
            "secret_handle",
            "scan_idempotency_key",
            "started_at",
            "implementation_version",
            "contract_version",
            "creation_authority",
            "architecture_version",
        ):
            _require_text(getattr(request, name), name)
        if request.secret_generation < 1 or request.context_format_version < 1:
            raise ValidationFailureError("context generation and format version must be positive")
        if not request.observations:
            raise ValidationFailureError("at least one structured observation is required")

        seen: set[str] = set()
        normalized: list[_NormalizedObservation] = []
        for observation in request.observations:
            for name in (
                "observation_key",
                "taxonomy_class",
                "authority_class",
                "observed_at",
                "privacy_class",
                "retention_policy",
            ):
                _require_text(getattr(observation, name), f"observation.{name}")
            if observation.observation_key in seen:
                raise ValidationFailureError("observation keys must be unique within a request")
            seen.add(observation.observation_key)
            if not isinstance(observation.payload, Mapping):
                raise ValidationFailureError("observation payload must be a JSON object")
            try:
                payload_json = json.dumps(
                    dict(observation.payload),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            except (TypeError, ValueError) as error:
                raise ValidationFailureError(
                    "observation payload must be canonical JSON data"
                ) from error
            normalized.append(
                _NormalizedObservation(
                    source=observation,
                    payload_json=payload_json,
                    immutable_digest=hashlib.sha256(payload_json.encode("utf-8")).digest(),
                )
            )
        return tuple(normalized)

    def _get_or_create_audit(
        self,
        repository: AuditRepository,
        *,
        installation_id: int,
        idempotency_key: str,
        event_kind: str,
        recorded_at: str,
        request: OperationalSliceRequest,
    ) -> int:
        audit = repository.get_by_idempotency(installation_id, idempotency_key)
        if audit is None:
            return repository.create(
                installation_id=installation_id,
                idempotency_key=idempotency_key,
                event_kind=event_kind,
                recorded_at=recorded_at,
                authority=request.creation_authority,
                provenance_ref=None,
                architecture_version=request.architecture_version,
                contract_version=request.contract_version,
                schema_version=CURRENT_SCHEMA_VERSION,
                implementation_version=request.implementation_version,
                outcome="SUCCEEDED",
                safe_failure_code=None,
            )
        _semantic_match(
            audit,
            {
                "installation_id": installation_id,
                "idempotency_key": idempotency_key,
                "event_kind": event_kind,
                "outcome": "SUCCEEDED",
                "safe_failure_code": None,
            },
            "audit record",
        )
        return int(audit["id"])

    @staticmethod
    def _audit_key(event_kind: str, intent: Mapping[str, object]) -> str:
        return f"operational:{event_kind.lower()}:{canonical_intent_digest(intent)}"

    @staticmethod
    def _completion_result(
        request: ScanCompletionRequest,
        *,
        capability_outcome_ids: tuple[int, ...],
        audit_id: int,
    ) -> ScanCompletionResult:
        return ScanCompletionResult(
            scan_run_id=request.scan_run_id,
            terminal_status=request.terminal_status,
            completeness=request.completeness,
            terminal_at=request.terminal_at,
            safe_error_code=request.safe_error_code,
            capability_outcome_ids=capability_outcome_ids,
            audit_id=audit_id,
            observation_ids=request.observation_ids,
        )
