from __future__ import annotations

from threading import RLock

from .models import RuntimeBundle


class RuntimeCache:
    """Process-local immutable cache keyed by aggregate bundle checksum."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._entries: dict[str, RuntimeBundle] = {}
        self._lock = RLock()

    def get(self, checksum: str) -> RuntimeBundle | None:
        if not self.enabled:
            return None
        with self._lock:
            return self._entries.get(checksum)

    def put(self, bundle: RuntimeBundle) -> None:
        if self.enabled:
            with self._lock:
                self._entries = {bundle.checksum: bundle}

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)
