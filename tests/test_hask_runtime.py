from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from hadocs.knowledge.hask_runtime import BundleManager, LifecycleState, RuntimeConfig
from hadocs.knowledge.hask_runtime.cache import RuntimeCache
from hadocs.knowledge.hask_runtime.discovery import BundleDiscovery
from hadocs.knowledge.hask_runtime.provider import KnowledgeProvider

BUNDLE = Path(r"D:\HA-Stability-Knowledge\dist\hadocs")
REQUIRED = tuple(sorted(path.name for path in BUNDLE.glob("*.json") if path.name != "manifest.json"))


def config(path: Path | None = BUNDLE, *, enabled: bool = True, cache: bool = True) -> RuntimeConfig:
    return RuntimeConfig(enabled, path, True, cache)


def copy_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "bundle"; shutil.copytree(BUNDLE, target); return target


def rewrite_manifest(path: Path, mutation) -> None:
    manifest_path = path / "manifest.json"; value = json.loads(manifest_path.read_text(encoding="utf-8")); mutation(value)
    manifest_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rehash_artifact(path: Path, name: str) -> None:
    manifest_path = path / "manifest.json"; manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][name] = hashlib.sha256((path / name).read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for artifact in REQUIRED:
        digest.update(artifact.encode()); digest.update(b"\0"); digest.update((path / artifact).read_bytes()); digest.update(b"\0")
    manifest["artifact_sha256"] = digest.hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_runtime_configuration_is_disabled_by_default(monkeypatch):
    for name in ("HADOCS_HASK_ENABLED", "HADOCS_HASK_BUNDLE_PATH", "HADOCS_HASK_STRICT_VALIDATION", "HADOCS_HASK_CACHE_ENABLED"):
        monkeypatch.delenv(name, raising=False)
    assert RuntimeConfig.from_environment() == RuntimeConfig(False, None, True, True)


def test_disabled_startup_has_no_provider_or_scan_impact():
    manager = BundleManager(RuntimeConfig())
    result = manager.startup()
    assert result.lifecycle_state == LifecycleState.DISABLED
    assert manager.provider.active is False


def test_enabled_startup_discovers_configured_bundle():
    manager = BundleManager(config())
    result = manager.startup()
    assert result.active and result.validation_status == "valid" and result.checksum_status == "valid"
    assert result.bundle_version == manager.provider.bundle.contract_version
    assert result.compatibility == "compatible_with_unknown_fields"
    assert manager.provider.items("platform_index.json")


def test_standard_discovery(tmp_path: Path):
    discovery = BundleDiscovery((BUNDLE, tmp_path / "missing"))
    assert discovery.discover().path == BUNDLE.resolve()


def test_missing_bundle_degrades_gracefully(tmp_path: Path):
    manager = BundleManager(config(tmp_path / "missing"))
    result = manager.startup()
    assert result.lifecycle_state == LifecycleState.DEGRADED
    assert result.graceful_degradation_reason == "bundle_missing"
    assert manager.provider.active is False


@pytest.mark.parametrize("filename", ["manifest.json", "platform_index.json"])
def test_corrupt_bundle_degrades_gracefully(tmp_path: Path, filename: str):
    path = copy_bundle(tmp_path); (path / filename).write_text("{", encoding="utf-8")
    result = BundleManager(config(path)).startup()
    assert result.lifecycle_state == LifecycleState.DEGRADED and result.validation_status == "failed"


def test_checksum_failure_is_diagnostic(tmp_path: Path):
    path = copy_bundle(tmp_path); (path / "readiness.json").write_bytes((path / "readiness.json").read_bytes() + b" ")
    result = BundleManager(config(path)).startup()
    assert result.checksum_status == "failed" and result.graceful_degradation_reason == "checksum_failed"


def test_incompatible_contract_is_diagnostic(tmp_path: Path):
    path = copy_bundle(tmp_path); rewrite_manifest(path, lambda item: item.update(contract_version="2.0.0"))
    result = BundleManager(config(path)).startup()
    assert result.graceful_degradation_reason == "incompatible_major_version"


def test_unsupported_hadocs_version_is_diagnostic(tmp_path: Path):
    path = copy_bundle(tmp_path); rewrite_manifest(path, lambda item: item.update(minimum_hadocs_version="99.0.0"))
    result = BundleManager(config(path)).startup()
    assert result.graceful_degradation_reason == "unsupported_hadocs_version"


def test_manifest_schema_failure_is_diagnostic(tmp_path: Path):
    path = copy_bundle(tmp_path); rewrite_manifest(path, lambda item: item.pop("knowledge_schema_version"))
    result = BundleManager(config(path)).startup()
    assert result.graceful_degradation_reason == "schema_failed"


def test_cache_miss_then_hit():
    manager = BundleManager(config())
    assert manager.startup().cache_status == "miss"
    assert manager.reload().cache_status == "hit"
    assert manager.cache.size == 1


def test_cache_can_be_disabled():
    manager = BundleManager(config(cache=False))
    assert manager.startup().cache_status == "disabled"
    assert manager.reload().cache_status == "disabled"
    assert manager.cache.size == 0


def test_cache_invalidation_uses_aggregate_checksum(tmp_path: Path):
    path = copy_bundle(tmp_path); manager = BundleManager(config(path)); first = manager.startup(); first_checksum = manager.provider.bundle.checksum
    name = "readiness.json"; data = json.loads((path / name).read_text(encoding="utf-8")); data["metadata"]["pilot_revision"] = 2
    (path / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"); rehash_artifact(path, name)
    second = manager.reload()
    assert second.cache_status == "miss" and manager.provider.bundle.checksum != first_checksum


def test_failed_reload_preserves_active_snapshot(tmp_path: Path):
    path = copy_bundle(tmp_path); manager = BundleManager(config(path)); manager.startup(); checksum = manager.provider.bundle.checksum
    (path / "platform_index.json").write_text("{", encoding="utf-8")
    result = manager.reload()
    assert result.active and result.cache_status == "preserved" and manager.provider.bundle.checksum == checksum


def test_deactivate_and_shutdown_lifecycle():
    manager = BundleManager(config()); manager.startup()
    assert manager.deactivate().lifecycle_state == LifecycleState.INACTIVE
    manager.startup(); result = manager.shutdown()
    assert result.lifecycle_state == LifecycleState.SHUTDOWN and not manager.provider.active and manager.cache.size == 0


def test_runtime_objects_are_immutable():
    manager = BundleManager(config()); manager.startup(); bundle = manager.provider.bundle
    with pytest.raises(TypeError):
        bundle.manifest["contract_version"] = "changed"


def test_provider_and_cache_are_injectable():
    provider = KnowledgeProvider(); cache = RuntimeCache(True)
    manager = BundleManager(config(), provider=provider, cache=cache)
    assert manager.startup().active and manager.provider is provider and manager.cache is cache


def test_runtime_never_modifies_source_bundle():
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in BUNDLE.iterdir() if path.is_file()}
    manager = BundleManager(config()); manager.startup(); manager.reload(); manager.shutdown()
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in BUNDLE.iterdir() if path.is_file()}
    assert before == after
