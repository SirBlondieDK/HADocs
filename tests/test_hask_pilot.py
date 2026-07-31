from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from hadocs.knowledge.hask_pilot import BundleError, PilotConfig, load_bundle, run_pilot
from hadocs.knowledge.hask_pilot.loader import REQUIRED, negotiate_version

HASK_BUNDLE = Path(r"D:\HA-Stability-Knowledge\dist\hadocs")
FIXTURES = Path(__file__).parent / "fixtures" / "hask_pilot"


def local(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def enabled(path: Path = HASK_BUNDLE) -> PilotConfig:
    return PilotConfig(True, path, True)


def copy_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "bundle"
    shutil.copytree(HASK_BUNDLE, target)
    return target


def rehash(path: Path, changed: str) -> None:
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][changed] = hashlib.sha256((path / changed).read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for name in sorted(REQUIRED):
        digest.update(name.encode()); digest.update(b"\0"); digest.update((path / name).read_bytes()); digest.update(b"\0")
    manifest["artifact_sha256"] = digest.hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_pilot_is_disabled_by_default(monkeypatch):
    for name in ("HADOCS_HASK_PILOT_ENABLED", "HADOCS_HASK_BUNDLE_PATH", "HADOCS_HASK_STRICT_VALIDATION"):
        monkeypatch.delenv(name, raising=False)
    config = PilotConfig.from_environment()
    assert config == PilotConfig(False, None, True)
    assert run_pilot("unifi", [], config) == {"status": "pilot_disabled", "platform": "unifi", "scan_impact": "none"}


def test_enabled_pilot_requires_bundle_path():
    with pytest.raises(BundleError) as error:
        run_pilot("unifi", [], PilotConfig(True, None, True))
    assert error.value.status == "bundle_path_missing"


def test_valid_bundle_and_version_negotiation():
    bundle = load_bundle(HASK_BUNDLE)
    assert negotiate_version(bundle.manifest["contract_version"]) == "compatible_with_unknown_fields"
    assert negotiate_version("1.0.0") == "compatible"
    assert negotiate_version("1.1.0") == "compatible_with_unknown_fields"
    assert negotiate_version("2.0.0") == "incompatible_major_version"


@pytest.mark.parametrize("platform,fixture", [("unifi", "unifi_local_evidence.json"), ("mikrotik", "mikrotik_local_evidence.json")])
def test_vertical_pilot_is_candidate_only(platform: str, fixture: str):
    result = run_pilot(platform, local(fixture), enabled())
    assert result["status"] == "candidate_only"
    assert result["candidates"]
    assert result["confirmed_candidates"] == []
    assert result["health_score_impact"] is None
    assert result["production_scoring_changed"] is False
    assert all(candidate["confirmed"] is False for candidate in result["candidates"])
    assert all(candidate["provenance"] for candidate in result["candidates"])
    assert all(candidate["missing_evidence"] for candidate in result["candidates"])
    assert any(candidate["verification"] for candidate in result["candidates"])


def test_unknown_local_evidence_is_no_match():
    result = run_pilot("unifi", [{"evidence_id": "not_known", "state": "unknown"}], enabled())
    assert result["canonical_evidence"][0]["status"] == "no_match"
    assert result["status"] == "no_root_cause_candidate"


def test_unavailable_never_confirms_root_cause():
    result = run_pilot("unifi", [{"evidence_id": "entity_unavailable", "state": "observed"}], enabled())
    assert result["confirmed_candidates"] == []


def test_corrupt_checksum_is_rejected(tmp_path: Path):
    path = copy_bundle(tmp_path)
    (path / "platform_index.json").write_bytes((path / "platform_index.json").read_bytes() + b" ")
    with pytest.raises(BundleError) as error:
        load_bundle(path)
    assert error.value.status == "checksum_failed"


def test_missing_file_is_rejected(tmp_path: Path):
    path = copy_bundle(tmp_path)
    (path / "recommendations.json").unlink()
    with pytest.raises(BundleError) as error:
        load_bundle(path)
    assert error.value.status == "incomplete_bundle"


def test_invalid_manifest_is_rejected(tmp_path: Path):
    path = copy_bundle(tmp_path)
    (path / "manifest.json").write_text("{", encoding="utf-8")
    with pytest.raises(BundleError) as error:
        load_bundle(path)
    assert error.value.status == "schema_failed"


def test_unsupported_major_is_rejected(tmp_path: Path):
    path = copy_bundle(tmp_path)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8")); manifest["contract_version"] = "2.0.0"
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BundleError) as error:
        load_bundle(path)
    assert error.value.status == "incompatible_major_version"


def test_unresolved_reference_is_rejected_after_valid_checksum(tmp_path: Path):
    path = copy_bundle(tmp_path)
    name = "platform_index.json"; data = json.loads((path / name).read_text(encoding="utf-8"))
    data["items"][0].setdefault("references", {}).setdefault("observations", []).append("missing_id")
    (path / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"); rehash(path, name)
    with pytest.raises(BundleError) as error:
        load_bundle(path)
    assert error.value.status == "unresolved_reference"


def test_unknown_additive_field_is_preserved(tmp_path: Path):
    path = copy_bundle(tmp_path)
    name = "platform_index.json"; data = json.loads((path / name).read_text(encoding="utf-8"))
    data["pilot_unknown_field"] = {"preserved": True}
    (path / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"); rehash(path, name)
    assert load_bundle(path).artifacts[name]["pilot_unknown_field"] == {"preserved": True}


def test_conflicts_unknown_applicability_and_partial_verification_remain_visible():
    bundle = load_bundle(HASK_BUNDLE)
    assert bundle.items("conflicts.json")
    assert any("unknown" in json.dumps(item) for item in bundle.items("applicability.json"))
    assert any(item["verification_status"] == "incomplete" for item in bundle.items("verification_paths.json"))


def test_duplicate_candidates_are_deduplicated_by_id():
    result = run_pilot("unifi", local("unifi_local_evidence.json") * 2, enabled())
    ids = [candidate["candidate_id"] for candidate in result["candidates"]]
    assert len(ids) == len(set(ids))


def test_bundle_directory_is_not_modified():
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in HASK_BUNDLE.iterdir() if path.is_file()}
    run_pilot("unifi", local("unifi_local_evidence.json"), enabled())
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in HASK_BUNDLE.iterdir() if path.is_file()}
    assert before == after
