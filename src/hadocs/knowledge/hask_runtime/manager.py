from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from threading import RLock

from hadocs.knowledge.hask_pilot.loader import BundleError

from .cache import RuntimeCache
from .config import RuntimeConfig
from .discovery import BundleDiscovery, DiscoveryResult
from .models import RuntimeBundle, RuntimeDiagnostics, TypedMatcherContract, freeze
from .provider import KnowledgeProvider
from .validation import ContractValidator


class LifecycleState(StrEnum):
    DISABLED = "disabled"
    INACTIVE = "inactive"
    ACTIVE = "active"
    DEGRADED = "degraded"
    SHUTDOWN = "shutdown"


class BundleManager:
    def __init__(
        self,
        config: RuntimeConfig,
        discovery: BundleDiscovery | None = None,
        validator: ContractValidator | None = None,
        cache: RuntimeCache | None = None,
        provider: KnowledgeProvider | None = None,
    ) -> None:
        self.config = config
        self.discovery = discovery or BundleDiscovery()
        self.validator = validator or ContractValidator()
        self.cache = cache or RuntimeCache(config.cache_enabled)
        self.provider = provider or KnowledgeProvider()
        self._lock = RLock()
        self._diagnostics = self._status(LifecycleState.DISABLED if not config.enabled else LifecycleState.INACTIVE)

    def _status(self, state: LifecycleState, discovery: DiscoveryResult | None = None, **changes) -> RuntimeDiagnostics:
        values = {
            "enabled": self.config.enabled, "lifecycle_state": state.value, "active": self.provider.active,
            "discovery_status": discovery.status if discovery else "not_run", "discovery_source": discovery.source if discovery else "none",
            "bundle_path": str(discovery.path) if discovery and discovery.path else None, "bundle_version": None,
            "checksum_status": "not_checked", "compatibility": "not_checked", "validation_status": "not_checked",
            "cache_status": "disabled" if not self.cache.enabled else "empty", "trust_status": "not_checked",
            "graceful_degradation_reason": None,
        }
        values.update(changes)
        return RuntimeDiagnostics(**values)

    def startup(self) -> RuntimeDiagnostics:
        if not self.config.enabled:
            self._diagnostics = self._status(LifecycleState.DISABLED)
            return self._diagnostics
        return self.reload()

    def reload(self) -> RuntimeDiagnostics:
        with self._lock:
            discovery = self.discovery.discover(self.config.bundle_path)
            if discovery.path is None:
                return self._degrade(discovery, "bundle_missing")
            try:
                raw, compatibility, trust = self.validator.validate(discovery.path, strict=self.config.strict_validation)
                checksum = raw.manifest["artifact_sha256"]
                runtime = self.cache.get(checksum)
                cache_status = "hit" if runtime else ("disabled" if not self.cache.enabled else "miss")
                if runtime is None:
                    runtime = RuntimeBundle(checksum, raw.manifest["contract_version"], freeze(raw.manifest), freeze(raw.artifacts))
                    self.cache.put(runtime)
                self.provider.activate(runtime)
                self._diagnostics = self._status(
                    LifecycleState.ACTIVE, discovery, active=True, bundle_version=runtime.contract_version,
                    checksum_status="valid", compatibility=compatibility, validation_status="valid",
                    cache_status=cache_status, trust_status=trust,
                )
                return self._diagnostics
            except BundleError as exc:
                return self._degrade(discovery, exc.status)

    def _degrade(self, discovery: DiscoveryResult, reason: str) -> RuntimeDiagnostics:
        # A failed reload preserves an already-active immutable snapshot.
        state = LifecycleState.ACTIVE if self.provider.active else LifecycleState.DEGRADED
        self._diagnostics = self._status(
            state, discovery, active=self.provider.active, bundle_version=self.provider.bundle.contract_version if self.provider.bundle else None,
            checksum_status="failed" if "checksum" in reason else "not_valid", compatibility=reason if "version" in reason else "unknown",
            validation_status="failed", cache_status="preserved" if self.provider.active else ("disabled" if not self.cache.enabled else "empty"),
            trust_status="unverified", graceful_degradation_reason=reason,
        )
        return self._diagnostics

    def deactivate(self) -> RuntimeDiagnostics:
        with self._lock:
            self.provider.deactivate()
            self._diagnostics = self._status(LifecycleState.INACTIVE)
            return self._diagnostics

    def shutdown(self) -> RuntimeDiagnostics:
        with self._lock:
            self.provider.deactivate(); self.cache.clear()
            self._diagnostics = self._status(LifecycleState.SHUTDOWN)
            return self._diagnostics

    @property
    def diagnostics(self) -> RuntimeDiagnostics:
        return self._diagnostics

    def typed_matcher_contracts(self) -> tuple[TypedMatcherContract, ...]:
        if not self.provider.active:
            return ()
        try:
            return self.provider.typed_matcher_contracts()
        except ValueError as exc:
            raise BundleError(
                "schema_failed", "typed matcher contract validation failed"
            ) from exc
