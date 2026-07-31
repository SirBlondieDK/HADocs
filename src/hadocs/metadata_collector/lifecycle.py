"""Disabled-by-default snapshot lifecycle and scheduling infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from threading import RLock
from typing import Callable

from .contract import Producer, Snapshot, Source
from .errors import LifecycleError
from .normalization import Normalizer
from .registry import CapabilityRegistry
from .serialization import SnapshotSerializer


class LifecycleState(str, Enum):
    INACTIVE = "inactive"
    NEGOTIATING = "negotiating"
    COLLECTING = "collecting"
    NORMALIZING = "normalizing"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    enabled: bool = False
    scheduled_refresh_enabled: bool = False
    refresh_interval_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.refresh_interval_seconds is not None and self.refresh_interval_seconds <= 0:
            raise ValueError("refresh_interval_seconds must be positive")
        if self.scheduled_refresh_enabled and self.refresh_interval_seconds is None:
            raise ValueError("scheduled refresh requires an interval")


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    snapshot_id: str
    observed_at: str
    producer: Producer
    source: Source


class RefreshScheduler:
    """Scheduling policy holder; starts no thread and performs no I/O."""

    def __init__(self, config: CollectorConfig) -> None:
        self.config = config

    @property
    def interval_seconds(self) -> int | None:
        return self.config.refresh_interval_seconds if self.config.scheduled_refresh_enabled else None


class CollectorLifecycle:
    def __init__(
        self,
        config: CollectorConfig | None = None,
        capabilities: CapabilityRegistry | None = None,
        normalizer: Normalizer | None = None,
        serializer: SnapshotSerializer | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config or CollectorConfig()
        self.capabilities = capabilities or CapabilityRegistry()
        self.normalizer = normalizer or Normalizer()
        self.serializer = serializer or SnapshotSerializer(self.normalizer)
        self.logger = logger or logging.getLogger("hadocs.metadata_collector")
        self.scheduler = RefreshScheduler(self.config)
        self._state = LifecycleState.INACTIVE
        self._active_snapshot: Snapshot | None = None
        self._lock = RLock()

    @property
    def state(self) -> LifecycleState:
        return self._state

    @property
    def active_snapshot(self) -> Snapshot | None:
        return self._active_snapshot

    def startup(self) -> LifecycleState:
        self._state = LifecycleState.NEGOTIATING if self.config.enabled else LifecycleState.INACTIVE
        return self._state

    def execute_empty_snapshot(self, context: ExecutionContext) -> Snapshot:
        """Exercise infrastructure only; prohibited when any capability is registered."""
        with self._lock:
            if not self.config.enabled:
                raise LifecycleError("collector_disabled")
            if self.capabilities.size:
                raise LifecycleError("capability_execution_not_authorized_in_i001a")
            self._state = LifecycleState.COLLECTING
            candidate = Snapshot(
                snapshot_id=context.snapshot_id,
                observed_at=context.observed_at,
                producer=context.producer,
                source=context.source,
            )
            self._state = LifecycleState.NORMALIZING
            self._active_snapshot = self.normalizer.normalize(candidate)
            self._state = LifecycleState.READY
            return self._active_snapshot

    def serialize_active(self) -> bytes:
        if self._active_snapshot is None:
            raise LifecycleError("snapshot_not_ready")
        return self.serializer.serialize(self._active_snapshot)

    def deactivate(self) -> LifecycleState:
        with self._lock:
            self._active_snapshot = None
            self._state = LifecycleState.INACTIVE
            return self._state

    shutdown = deactivate

