from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
import sqlite3
from threading import Lock, get_ident
import time
from typing import Callable

from .coordination import IdempotencyCoordinator, RecoveryCoordinator
from .errors import (
    ConcurrencyConflictError, ConstraintViolationError, CorruptionDetectedError,
    NestedTransactionError, RepositoryError, StorageFailureError,
)
from .repositories import RepositoryFactory
from .repository_contracts import RepositoryContract, RepositoryOwner, validate_frozen_ownership
from .uow_contracts import UnitOfWorkContract


def translate_sqlite_error(error: sqlite3.Error) -> RepositoryError:
    message = str(error).lower()
    if isinstance(error, sqlite3.IntegrityError):
        return ConstraintViolationError("a frozen database constraint rejected the operation")
    if "locked" in message or "busy" in message:
        return ConcurrencyConflictError("the serialized SQLite writer is unavailable")
    if "malformed" in message or "not a database" in message or "corrupt" in message:
        return CorruptionDetectedError("SQLite integrity failure detected")
    return StorageFailureError("SQLite storage operation failed")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 4
    delays_ms: tuple[int, ...] = (25, 57, 119)
    timeout_ms: int = 500

    def __post_init__(self) -> None:
        if self.attempts != len(self.delays_ms) + 1 or self.attempts < 1:
            raise ValueError("attempts must equal one initial attempt plus the retry delays")
        if any(delay < 0 for delay in self.delays_ms) or sum(self.delays_ms) > self.timeout_ms:
            raise ValueError("retry schedule exceeds its timeout")


class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    def __init__(
        self,
        manager: "SerializedTransactionManager",
        contract: UnitOfWorkContract | None = None,
    ) -> None:
        self._manager = manager
        self.contract = contract
        self._repositories: dict[RepositoryOwner, RepositoryContract] = {}
        self.idempotency = IdempotencyCoordinator()
        self._active = False

    def __enter__(self) -> "UnitOfWork":
        self._manager._begin(self)
        try:
            if self.contract is None:
                self._repositories = self._manager.repository_factory.create_all(
                    self._manager._connection
                )
            else:
                self._repositories = {
                    owner: self._manager.repository_factory.create(
                        owner, self._manager._connection
                    )
                    for owner in self.contract.repository_owners
                }
            self._active = True
            return self
        except Exception:
            self._manager._rollback(self)
            raise

    def repository(self, owner: RepositoryOwner) -> RepositoryContract:
        if not self._active:
            raise NestedTransactionError("repository resolution requires an active Unit of Work")
        return self._repositories[owner]

    @property
    def repositories(self) -> tuple[RepositoryContract, ...]:
        owners = (
            self.contract.repository_owners
            if self.contract is not None
            else tuple(sorted(self._repositories, key=lambda item: item.value))
        )
        return tuple(self._repositories[owner] for owner in owners)

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            if exc_type is None:
                self._manager._commit(self)
            else:
                self._manager._rollback(self)
        finally:
            self._active = False
            self._repositories = {}
        return False


class SerializedTransactionManager:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        repository_factory: RepositoryFactory | None = None,
        recovery: RecoveryCoordinator | None = None,
        retry_policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._connection = connection
        self.repository_factory = repository_factory or RepositoryFactory()
        self.recovery = recovery or RecoveryCoordinator()
        self.retry_policy = retry_policy or RetryPolicy()
        self._sleeper = sleeper
        self._writer_lock = Lock()
        self._owner_thread: int | None = None
        self._active_uow: UnitOfWork | None = None
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        validate_frozen_ownership(frozenset(str(row[0]) for row in rows))

    def unit_of_work(self, contract: UnitOfWorkContract | None = None) -> UnitOfWork:
        return UnitOfWork(self, contract)

    def _begin(self, unit: UnitOfWork) -> None:
        self.recovery.assert_writable()
        if self._active_uow is not None or self._owner_thread == get_ident():
            raise NestedTransactionError("nested Unit of Work is prohibited")
        if not self._writer_lock.acquire(blocking=False):
            raise ConcurrencyConflictError("another Unit of Work owns the serialized writer")
        self._owner_thread = get_ident()
        try:
            for attempt in range(self.retry_policy.attempts):
                try:
                    self._connection.execute("BEGIN IMMEDIATE")
                    self._active_uow = unit
                    return
                except sqlite3.OperationalError as error:
                    translated = translate_sqlite_error(error)
                    if (
                        not isinstance(translated, ConcurrencyConflictError)
                        or attempt == self.retry_policy.attempts - 1
                    ):
                        raise translated from error
                    self._sleeper(self.retry_policy.delays_ms[attempt] / 1000)
        except Exception:
            self._release()
            raise

    def _commit(self, unit: UnitOfWork) -> None:
        self._assert_owner(unit)
        try:
            self._connection.commit()
        except sqlite3.Error as error:
            self._connection.rollback()
            self.recovery.require_recovery()
            raise translate_sqlite_error(error) from error
        finally:
            self._release()

    def _rollback(self, unit: UnitOfWork) -> None:
        self._assert_owner(unit)
        try:
            self._connection.rollback()
        except sqlite3.Error as error:
            self.recovery.require_recovery()
            raise translate_sqlite_error(error) from error
        finally:
            self._release()

    def _assert_owner(self, unit: UnitOfWork) -> None:
        if self._active_uow is not unit or self._owner_thread != get_ident():
            raise NestedTransactionError("Unit of Work does not own this transaction")

    def _release(self) -> None:
        self._active_uow = None
        self._owner_thread = None
        if self._writer_lock.locked():
            self._writer_lock.release()
