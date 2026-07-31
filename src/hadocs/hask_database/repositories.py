from __future__ import annotations

import sqlite3

from .errors import ConstraintViolationError, StorageFailureError
from .repository_contracts import FROZEN_OWNERSHIP, RepositoryContract, RepositoryDescriptor, RepositoryOwner


def _one(cursor: sqlite3.Cursor) -> dict[str, object] | None:
    row = cursor.fetchone()
    if row is None:
        return None
    names = tuple(item[0] for item in cursor.description or ())
    return dict(zip(names, row, strict=True))


def _all(cursor: sqlite3.Cursor) -> tuple[dict[str, object], ...]:
    names = tuple(item[0] for item in cursor.description or ())
    return tuple(dict(zip(names, row, strict=True)) for row in cursor.fetchall())


def _insert(connection: sqlite3.Connection, sql: str, parameters: tuple[object, ...]) -> int:
    try:
        cursor = connection.execute(sql, parameters)
    except sqlite3.IntegrityError as error:
        raise ConstraintViolationError(
            "a frozen database constraint rejected the repository operation"
        ) from error
    except sqlite3.Error as error:
        raise StorageFailureError("SQLite repository operation failed") from error
    return int(cursor.lastrowid)


def _update(connection: sqlite3.Connection, sql: str, parameters: tuple[object, ...]) -> int:
    try:
        cursor = connection.execute(sql, parameters)
    except sqlite3.IntegrityError as error:
        raise ConstraintViolationError(
            "a frozen database constraint rejected the repository transition"
        ) from error
    except sqlite3.Error as error:
        raise StorageFailureError("SQLite repository transition failed") from error
    return int(cursor.rowcount)


class BaseRepository:
    OWNER: RepositoryOwner
    PERMITS_BUSINESS_PERSISTENCE = False

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._descriptor = RepositoryDescriptor(
            self.OWNER,
            FROZEN_OWNERSHIP[self.OWNER],
            permits_business_persistence=self.PERMITS_BUSINESS_PERSISTENCE,
        )

    @property
    def descriptor(self) -> RepositoryDescriptor:
        return self._descriptor


class LogicalInstallationRepository(BaseRepository):
    OWNER = RepositoryOwner.LOGICAL_INSTALLATION
    PERMITS_BUSINESS_PERSISTENCE = True

    def get_installation(self, installation_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM logical_installation WHERE id=?", (installation_id,)
        ))

    def get_by_recovery_set_ref(self, recovery_set_ref: str) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM logical_installation WHERE recovery_set_ref=?",
            (recovery_set_ref,),
        ))

    def create_installation(
        self,
        *,
        state: str,
        created_at: str,
        creation_authority: str,
        recovery_set_ref: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO logical_installation("
            "state,created_at,retired_at,creation_authority,recovery_set_ref,current_context_id"
            ") VALUES(?,?,NULL,?,?,NULL)",
            (state, created_at, creation_authority, recovery_set_ref),
        )

    def get_context(self, context_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM installation_context WHERE id=?", (context_id,)
        ))

    def get_context_by_identity(
        self,
        *,
        installation_id: int,
        installation_scope: str,
        secret_generation: int,
        format_version: int,
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM installation_context WHERE installation_id=? "
            "AND installation_scope=? AND secret_generation=? AND format_version=?",
            (installation_id, installation_scope, secret_generation, format_version),
        ))

    def create_context(
        self,
        *,
        installation_id: int,
        installation_scope: str,
        secret_handle: str,
        secret_generation: int,
        format_version: int,
        valid_from: str,
        activation_audit_id: int,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO installation_context("
            "installation_id,predecessor_context_id,installation_scope,secret_handle,"
            "secret_generation,format_version,status,valid_from,valid_until,activation_audit_id"
            ") VALUES(?,NULL,?,?,?,?, 'ACTIVE',?,NULL,?)",
            (
                installation_id,
                installation_scope,
                secret_handle,
                secret_generation,
                format_version,
                valid_from,
                activation_audit_id,
            ),
        )

    def set_current_context(self, installation_id: int, context_id: int) -> None:
        try:
            cursor = self._connection.execute(
                "UPDATE logical_installation SET current_context_id=? "
                "WHERE id=? AND current_context_id IS NULL",
                (context_id, installation_id),
            )
        except sqlite3.IntegrityError as error:
            raise ConstraintViolationError(
                "a frozen database constraint rejected the current context"
            ) from error
        if cursor.rowcount != 1:
            raise ConstraintViolationError("logical installation already has a current context")


class CollisionRegistryRepository(BaseRepository):
    OWNER = RepositoryOwner.COLLISION_REGISTRY
    PERMITS_BUSINESS_PERSISTENCE = True

    def get_registry_for_installation(
        self, installation_id: int
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM collision_registry WHERE installation_id=?",
            (installation_id,),
        ))

    def create_registry(
        self, *, installation_id: int, format_version: int, created_at: str
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO collision_registry(installation_id,integrity_status,"
            "availability_status,format_version,created_at) VALUES(?,'VALID','AVAILABLE',?,?)",
            (installation_id, format_version, created_at),
        )

    def get_registration(self, registration_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM identity_registration WHERE id=?", (registration_id,)
        ))

    def get_registration_by_tuple(
        self,
        *,
        registry_id: int,
        context_id: int,
        reference_kind: str,
        format_version: int,
        canonical_tuple_handle: str,
        secret_generation: int,
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM identity_registration WHERE registry_id=? AND context_id=? "
            "AND reference_kind=? AND format_version=? AND canonical_tuple_handle=? "
            "AND secret_generation=?",
            (
                registry_id,
                context_id,
                reference_kind,
                format_version,
                canonical_tuple_handle,
                secret_generation,
            ),
        ))

    def get_registration_by_reference(
        self,
        *,
        registry_id: int,
        context_id: int,
        reference_kind: str,
        format_version: int,
        opaque_reference: str,
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM identity_registration WHERE registry_id=? AND context_id=? "
            "AND reference_kind=? AND format_version=? AND opaque_reference=?",
            (registry_id, context_id, reference_kind, format_version, opaque_reference),
        ))

    def create_registration(
        self,
        *,
        registry_id: int,
        context_id: int,
        reference_kind: str,
        format_version: int,
        canonical_tuple_handle: str,
        opaque_reference: str,
        secret_generation: int,
        registered_at: str,
        registration_audit_id: int,
        identity_digest: bytes,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO identity_registration(registry_id,context_id,reference_kind,"
            "format_version,canonical_tuple_handle,opaque_reference,secret_generation,status,"
            "registered_at,retired_at,registration_audit_id,identity_digest) "
            "VALUES(?,?,?,?,?,?,?,'ACTIVE',?,NULL,?,?)",
            (
                registry_id,
                context_id,
                reference_kind,
                format_version,
                canonical_tuple_handle,
                opaque_reference,
                secret_generation,
                registered_at,
                registration_audit_id,
                identity_digest,
            ),
        )

    def list_registrations_for_installation(
        self, installation_id: int
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT ir.* FROM identity_registration ir "
            "JOIN collision_registry cr ON cr.id=ir.registry_id "
            "WHERE cr.installation_id=? ORDER BY ir.opaque_reference,ir.id",
            (installation_id,),
        ))


class EntityRepository(BaseRepository):
    OWNER = RepositoryOwner.ENTITY
    PERMITS_BUSINESS_PERSISTENCE = True

    def get(self, entity_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM entity WHERE id=?", (entity_id,)
        ))

    def get_by_registration(
        self, identity_registration_id: int
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM entity WHERE identity_registration_id=?",
            (identity_registration_id,),
        ))

    def create(
        self,
        *,
        installation_id: int,
        context_id: int,
        identity_registration_id: int,
        created_at: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO entity(installation_id,context_id,identity_registration_id,"
            "identity_status,created_at) VALUES(?,?,?,'ACTIVE',?)",
            (installation_id, context_id, identity_registration_id, created_at),
        )

    def list_for_installation(
        self, installation_id: int
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT e.*,ir.opaque_reference FROM entity e "
            "JOIN identity_registration ir ON ir.id=e.identity_registration_id "
            "WHERE e.installation_id=? ORDER BY ir.opaque_reference,e.id",
            (installation_id,),
        ))

    def list_for_scan(self, scan_run_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT DISTINCT e.*,ir.opaque_reference FROM entity e "
            "JOIN identity_registration ir ON ir.id=e.identity_registration_id "
            "JOIN entity_lifecycle_event ev ON ev.entity_id=e.id "
            "WHERE ev.scan_run_id=? ORDER BY ir.opaque_reference,e.id",
            (scan_run_id,),
        ))

    def get_current_state(self, entity_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM entity_current_state WHERE entity_id=?", (entity_id,)
        ))

    def get_event(self, event_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM entity_lifecycle_event WHERE id=?", (event_id,)
        ))

    def get_event_by_idempotency(
        self, entity_id: int, idempotency_key: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM entity_lifecycle_event WHERE entity_id=? AND idempotency_key=?",
            (entity_id, idempotency_key),
        ))

    def list_events(self, entity_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM entity_lifecycle_event WHERE entity_id=? ORDER BY event_at,id",
            (entity_id,),
        ))

    def create_event(
        self,
        *,
        entity_id: int,
        idempotency_key: str,
        prior_state: str | None,
        result_state: str,
        observation_id: int,
        scan_run_id: int,
        audit_id: int,
        event_at: str,
        reason_code: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO entity_lifecycle_event(entity_id,idempotency_key,prior_state,"
            "result_state,observation_id,scan_run_id,audit_id,event_at,reason_code) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                entity_id,
                idempotency_key,
                prior_state,
                result_state,
                observation_id,
                scan_run_id,
                audit_id,
                event_at,
                reason_code,
            ),
        )

    def create_current_state(
        self,
        *,
        entity_id: int,
        lifecycle_state: str,
        effective_at: str,
        source_event_id: int,
        scan_run_id: int,
        audit_id: int,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO entity_current_state(entity_id,lifecycle_state,effective_at,"
            "source_event_id,scan_run_id,audit_id) VALUES(?,?,?,?,?,?)",
            (entity_id, lifecycle_state, effective_at, source_event_id, scan_run_id, audit_id),
        )

    def transition_current_state(
        self,
        *,
        entity_id: int,
        expected_state: str,
        expected_source_event_id: int,
        lifecycle_state: str,
        effective_at: str,
        source_event_id: int,
        scan_run_id: int,
        audit_id: int,
    ) -> None:
        changed = _update(
            self._connection,
            "UPDATE entity_current_state SET lifecycle_state=?,effective_at=?,"
            "source_event_id=?,scan_run_id=?,audit_id=? WHERE entity_id=? "
            "AND lifecycle_state=? AND source_event_id=?",
            (
                lifecycle_state,
                effective_at,
                source_event_id,
                scan_run_id,
                audit_id,
                entity_id,
                expected_state,
                expected_source_event_id,
            ),
        )
        if changed != 1:
            raise ConstraintViolationError("entity current state changed concurrently")

class RelationshipRepository(BaseRepository):
    OWNER = RepositoryOwner.RELATIONSHIP
    PERMITS_BUSINESS_PERSISTENCE = True

    def get(self, relationship_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship WHERE id=?", (relationship_id,)
        ))

    def get_by_public_id(
        self, installation_id: int, public_relationship_id: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship WHERE installation_id=? "
            "AND public_relationship_id=?",
            (installation_id, public_relationship_id),
        ))

    def get_by_tuple(
        self,
        *,
        installation_id: int,
        predicate: str,
        source_ref: str,
        target_ref: str,
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship WHERE installation_id=? AND predicate=? "
            "AND source_ref=? AND target_ref=?",
            (installation_id, predicate, source_ref, target_ref),
        ))

    def create(
        self,
        *,
        installation_id: int,
        public_relationship_id: str,
        predicate: str,
        source_entity_id: int,
        source_ref: str,
        target_ref: str,
        created_at: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO relationship(installation_id,public_relationship_id,predicate,"
            "source_entity_id,source_ref,target_ref,identity_status,created_at) "
            "VALUES(?,?,?,?,?,?,'ACTIVE',?)",
            (
                installation_id,
                public_relationship_id,
                predicate,
                source_entity_id,
                source_ref,
                target_ref,
                created_at,
            ),
        )

    def list_for_installation(
        self, installation_id: int
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT r.*,rcs.status AS current_status FROM relationship r "
            "LEFT JOIN relationship_current_state rcs ON rcs.relationship_id=r.id "
            "WHERE r.installation_id=? ORDER BY r.public_relationship_id,r.id",
            (installation_id,),
        ))

    def list_for_scan(self, scan_run_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT DISTINCT r.* FROM relationship r "
            "JOIN relationship_lifecycle_event ev ON ev.relationship_id=r.id "
            "WHERE ev.scan_run_id=? ORDER BY r.public_relationship_id,r.id",
            (scan_run_id,),
        ))

    def list_for_source_entity(
        self, source_entity_id: int
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT r.*,rcs.status AS current_status FROM relationship r "
            "LEFT JOIN relationship_current_state rcs ON rcs.relationship_id=r.id "
            "WHERE r.source_entity_id=? ORDER BY r.public_relationship_id,r.id",
            (source_entity_id,),
        ))

    def get_current_state(self, relationship_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship_current_state WHERE relationship_id=?",
            (relationship_id,),
        ))

    def get_event(self, event_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship_lifecycle_event WHERE id=?", (event_id,)
        ))

    def get_event_by_idempotency(
        self, relationship_id: int, idempotency_key: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM relationship_lifecycle_event "
            "WHERE relationship_id=? AND idempotency_key=?",
            (relationship_id, idempotency_key),
        ))

    def list_events(self, relationship_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM relationship_lifecycle_event WHERE relationship_id=? "
            "ORDER BY event_at,id",
            (relationship_id,),
        ))

    def create_event(
        self,
        *,
        relationship_id: int,
        idempotency_key: str,
        event_kind: str,
        prior_predicate: str | None,
        prior_source_ref: str | None,
        prior_target_ref: str | None,
        result_predicate: str | None,
        result_source_ref: str | None,
        result_target_ref: str | None,
        continuity: str,
        observation_id: int,
        scan_run_id: int,
        audit_id: int,
        event_at: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO relationship_lifecycle_event(relationship_id,idempotency_key,"
            "event_kind,prior_predicate,prior_source_ref,prior_target_ref,result_predicate,"
            "result_source_ref,result_target_ref,continuity,observation_id,scan_run_id,"
            "audit_id,event_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                relationship_id,
                idempotency_key,
                event_kind,
                prior_predicate,
                prior_source_ref,
                prior_target_ref,
                result_predicate,
                result_source_ref,
                result_target_ref,
                continuity,
                observation_id,
                scan_run_id,
                audit_id,
                event_at,
            ),
        )

    def create_current_state(
        self,
        *,
        relationship_id: int,
        status: str,
        predicate: str | None,
        source_ref: str | None,
        target_ref: str | None,
        effective_at: str,
        source_event_id: int,
        scan_run_id: int,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO relationship_current_state(relationship_id,status,predicate,"
            "source_ref,target_ref,effective_at,source_event_id,scan_run_id) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                relationship_id,
                status,
                predicate,
                source_ref,
                target_ref,
                effective_at,
                source_event_id,
                scan_run_id,
            ),
        )

    def transition_current_state(
        self,
        *,
        relationship_id: int,
        expected_status: str,
        expected_source_event_id: int,
        status: str,
        predicate: str | None,
        source_ref: str | None,
        target_ref: str | None,
        effective_at: str,
        source_event_id: int,
        scan_run_id: int,
    ) -> None:
        changed = _update(
            self._connection,
            "UPDATE relationship_current_state SET status=?,predicate=?,source_ref=?,"
            "target_ref=?,effective_at=?,source_event_id=?,scan_run_id=? "
            "WHERE relationship_id=? AND status=? AND source_event_id=?",
            (
                status,
                predicate,
                source_ref,
                target_ref,
                effective_at,
                source_event_id,
                scan_run_id,
                relationship_id,
                expected_status,
                expected_source_event_id,
            ),
        )
        if changed != 1:
            raise ConstraintViolationError("relationship current state changed concurrently")


class ScanRunRepository(BaseRepository):
    OWNER = RepositoryOwner.SCAN_RUN
    PERMITS_BUSINESS_PERSISTENCE = True

    def get(self, scan_run_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM scan_run WHERE id=?", (scan_run_id,)
        ))

    def get_by_idempotency(
        self, installation_id: int, idempotency_key: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM scan_run WHERE installation_id=? AND idempotency_key=?",
            (installation_id, idempotency_key),
        ))

    def create_running(
        self,
        *,
        installation_id: int,
        context_id: int,
        idempotency_key: str,
        started_at: str,
        implementation_version: str,
        contract_version: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO scan_run("
            "installation_id,context_id,idempotency_key,started_at,terminal_at,status,"
            "completeness,safe_error_code,implementation_version,contract_version"
            ") VALUES(?,?,?,?,NULL,'RUNNING','PENDING',NULL,?,?)",
            (
                installation_id,
                context_id,
                idempotency_key,
                started_at,
                implementation_version,
                contract_version,
            ),
        )

    def list_capability_outcomes(
        self, scan_run_id: int
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM scan_capability_outcome WHERE scan_run_id=? "
            "ORDER BY capability_id,id",
            (scan_run_id,),
        ))

    def get_capability_outcome(
        self, scan_run_id: int, capability_id: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM scan_capability_outcome "
            "WHERE scan_run_id=? AND capability_id=?",
            (scan_run_id, capability_id),
        ))

    def get_capability_outcome_by_id(
        self, outcome_id: int
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM scan_capability_outcome WHERE id=?", (outcome_id,)
        ))

    def create_capability_outcome(
        self,
        *,
        scan_run_id: int,
        capability_id: str,
        status: str,
        retryable: bool | None,
        safe_error_code: str | None,
        observation_contribution: bool,
        completeness_contribution: str,
        recorded_at: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO scan_capability_outcome("
            "scan_run_id,capability_id,status,retryable,safe_error_code,"
            "observation_contribution,completeness_contribution,recorded_at"
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                scan_run_id,
                capability_id,
                status,
                None if retryable is None else int(retryable),
                safe_error_code,
                int(observation_contribution),
                completeness_contribution,
                recorded_at,
            ),
        )

    def terminalize(
        self,
        *,
        scan_run_id: int,
        terminal_at: str,
        status: str,
        completeness: str,
        safe_error_code: str | None,
    ) -> None:
        changed = _update(
            self._connection,
            "UPDATE scan_run SET terminal_at=?,status=?,completeness=?,safe_error_code=? "
            "WHERE id=? AND status='RUNNING'",
            (terminal_at, status, completeness, safe_error_code, scan_run_id),
        )
        if changed != 1:
            raise ConstraintViolationError("scan is not available for terminal transition")


class ObservationRepository(BaseRepository):
    OWNER = RepositoryOwner.OBSERVATION
    PERMITS_BUSINESS_PERSISTENCE = True

    def get(self, observation_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM observation WHERE id=?", (observation_id,)
        ))

    def list_for_run(self, scan_run_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM observation WHERE scan_run_id=? ORDER BY observation_key,id",
            (scan_run_id,),
        ))

    def get_by_key(self, scan_run_id: int, observation_key: str) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM observation WHERE scan_run_id=? AND observation_key=?",
            (scan_run_id, observation_key),
        ))

    def create(
        self,
        *,
        scan_run_id: int,
        observation_key: str,
        taxonomy_class: str,
        authority_class: str,
        provenance_ref: str | None,
        observed_at: str,
        normalized_payload_json: str,
        privacy_class: str,
        retention_policy: str,
        immutable_digest: bytes,
        created_at: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO observation("
            "scan_run_id,observation_key,taxonomy_class,authority_class,provenance_ref,"
            "observed_at,normalized_payload_json,privacy_class,retention_policy,"
            "immutable_digest,created_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                scan_run_id,
                observation_key,
                taxonomy_class,
                authority_class,
                provenance_ref,
                observed_at,
                normalized_payload_json,
                privacy_class,
                retention_policy,
                immutable_digest,
                created_at,
            ),
        )


class CompatibilityDecisionRepository(BaseRepository): OWNER = RepositoryOwner.COMPATIBILITY_DECISION


class AuditRepository(BaseRepository):
    OWNER = RepositoryOwner.AUDIT
    PERMITS_BUSINESS_PERSISTENCE = True

    def get(self, audit_id: int) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM audit_record WHERE id=?", (audit_id,)
        ))

    def get_by_idempotency(
        self, installation_id: int, idempotency_key: str
    ) -> dict[str, object] | None:
        return _one(self._connection.execute(
            "SELECT * FROM audit_record WHERE installation_id=? AND idempotency_key=?",
            (installation_id, idempotency_key),
        ))

    def list_for_installation(self, installation_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM audit_record WHERE installation_id=? ORDER BY id",
            (installation_id,),
        ))

    def create(
        self,
        *,
        installation_id: int,
        idempotency_key: str,
        event_kind: str,
        recorded_at: str,
        authority: str,
        provenance_ref: str | None,
        architecture_version: str,
        contract_version: str,
        schema_version: int,
        implementation_version: str,
        outcome: str,
        safe_failure_code: str | None,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO audit_record("
            "installation_id,idempotency_key,event_kind,recorded_at,authority,provenance_ref,"
            "architecture_version,contract_version,schema_version,implementation_version,"
            "outcome,safe_failure_code"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                installation_id,
                idempotency_key,
                event_kind,
                recorded_at,
                authority,
                provenance_ref,
                architecture_version,
                contract_version,
                schema_version,
                implementation_version,
                outcome,
                safe_failure_code,
            ),
        )

    def list_for_subject(
        self,
        *,
        subject_kind: str,
        subject_id: int,
        role: str,
    ) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT ar.* FROM audit_record ar "
            "JOIN audit_subject_link asl ON asl.audit_id=ar.id "
            "WHERE asl.subject_kind=? AND asl.subject_id=? AND asl.role=? "
            "ORDER BY ar.id",
            (subject_kind, subject_id, role),
        ))

    def list_subject_links(self, audit_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM audit_subject_link WHERE audit_id=? "
            "ORDER BY subject_kind,subject_id,role,id",
            (audit_id,),
        ))

    def create_subject_link(
        self,
        *,
        audit_id: int,
        subject_kind: str,
        subject_id: int,
        role: str,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO audit_subject_link(audit_id,subject_kind,subject_id,role) "
            "VALUES(?,?,?,?)",
            (audit_id, subject_kind, subject_id, role),
        )

    def list_evidence_links(self, audit_id: int) -> tuple[dict[str, object], ...]:
        return _all(self._connection.execute(
            "SELECT * FROM audit_evidence_link WHERE audit_id=? ORDER BY ordinal,id",
            (audit_id,),
        ))

    def create_evidence_link(
        self,
        *,
        audit_id: int,
        observation_id: int,
        role: str,
        ordinal: int,
    ) -> int:
        return _insert(
            self._connection,
            "INSERT INTO audit_evidence_link(audit_id,observation_id,role,ordinal) "
            "VALUES(?,?,?,?)",
            (audit_id, observation_id, role, ordinal),
        )


class VersionStateRepository(BaseRepository): OWNER = RepositoryOwner.VERSION_STATE
class MigrationStateRepository(BaseRepository): OWNER = RepositoryOwner.MIGRATION_STATE


RepositoryType = type[BaseRepository]


class RepositoryRegistry:
    def __init__(self) -> None:
        self._types: dict[RepositoryOwner, RepositoryType] = {}

    def register(self, repository_type: RepositoryType) -> None:
        owner = repository_type.OWNER
        if owner in self._types:
            raise ValueError(f"duplicate repository owner: {owner.value}")
        self._types[owner] = repository_type

    def validate_complete(self) -> None:
        if set(self._types) != set(RepositoryOwner):
            raise ValueError("repository registry must contain exactly the ten frozen owners")

    @property
    def owners(self) -> tuple[RepositoryOwner, ...]:
        return tuple(sorted(self._types, key=lambda item: item.value))

    def resolve_type(self, owner: RepositoryOwner) -> RepositoryType:
        try:
            return self._types[owner]
        except KeyError as error:
            raise KeyError(f"repository owner is not registered: {owner.value}") from error


DEFAULT_REPOSITORY_TYPES: tuple[RepositoryType, ...] = (
    LogicalInstallationRepository, CollisionRegistryRepository, EntityRepository,
    RelationshipRepository, ScanRunRepository, ObservationRepository,
    CompatibilityDecisionRepository, AuditRepository, VersionStateRepository,
    MigrationStateRepository,
)


def default_repository_registry() -> RepositoryRegistry:
    registry = RepositoryRegistry()
    for repository_type in DEFAULT_REPOSITORY_TYPES:
        registry.register(repository_type)
    registry.validate_complete()
    return registry


class RepositoryFactory:
    def __init__(self, registry: RepositoryRegistry | None = None) -> None:
        self.registry = registry or default_repository_registry()
        self.registry.validate_complete()

    def create(self, owner: RepositoryOwner, connection: sqlite3.Connection) -> RepositoryContract:
        return self.registry.resolve_type(owner)(connection)

    def create_all(self, connection: sqlite3.Connection) -> dict[RepositoryOwner, RepositoryContract]:
        return {owner: self.create(owner, connection) for owner in self.registry.owners}
