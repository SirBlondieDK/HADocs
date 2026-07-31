from __future__ import annotations

from enum import Enum
import hashlib
import json
from threading import RLock
from typing import Mapping

from .errors import IdempotencyConflictError, RecoveryModeError


def canonical_intent_digest(intent: Mapping[str, object]) -> str:
    payload = json.dumps(intent, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class IdempotencyCoordinator:
    """Transaction-local intent equality guard; it persists no state."""

    def __init__(self) -> None:
        self._intents: dict[tuple[str, str], str] = {}

    def claim(self, scope: str, key: str, intent: Mapping[str, object]) -> bool:
        identity = (scope, key)
        digest = canonical_intent_digest(intent)
        previous = self._intents.get(identity)
        if previous is None:
            self._intents[identity] = digest
            return True
        if previous != digest:
            raise IdempotencyConflictError("idempotency key has conflicting normalized intent")
        return False


class RecoveryState(str, Enum):
    NORMAL = "NORMAL"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    VALIDATING = "VALIDATING"


class RecoveryCoordinator:
    def __init__(self) -> None:
        self._state = RecoveryState.NORMAL
        self._lock = RLock()

    @property
    def state(self) -> RecoveryState:
        return self._state

    def require_recovery(self) -> None:
        with self._lock:
            self._state = RecoveryState.RECOVERY_REQUIRED

    def begin_validation(self) -> None:
        with self._lock:
            if self._state is not RecoveryState.RECOVERY_REQUIRED:
                raise RecoveryModeError("recovery validation requires recovery mode")
            self._state = RecoveryState.VALIDATING

    def validation_passed(self) -> None:
        with self._lock:
            if self._state is not RecoveryState.VALIDATING:
                raise RecoveryModeError("recovery validation is not active")
            self._state = RecoveryState.NORMAL

    def validation_failed(self) -> None:
        with self._lock:
            if self._state is not RecoveryState.VALIDATING:
                raise RecoveryModeError("recovery validation is not active")
            self._state = RecoveryState.RECOVERY_REQUIRED

    def assert_writable(self) -> None:
        if self._state is not RecoveryState.NORMAL:
            raise RecoveryModeError("repository transactions are disabled in recovery mode")
