from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from hadocs.knowledge.hask_pilot.loader import REQUIRED, load_bundle
from hadocs.knowledge.hask_runtime.validation import ContractValidator
from scripts.build_hadocs_contract import BundleBuildError, build_bundle


ROOT = Path(__file__).resolve().parents[1]
PACKAGED_ROOT = ROOT / "src" / "hadocs" / "knowledge" / "hask_bundle"
SOURCE = ROOT / "scripts" / "hask_bundle_sources" / "0.2.1.json"


def _copy_base(tmp_path: Path) -> Path:
    target = tmp_path / "hask_bundle"
    shutil.copytree(PACKAGED_ROOT / "0.2.0", target / "0.2.0")
    return target


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.glob("*.json")):
        digest.update(item.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _source_copy(tmp_path: Path) -> dict[str, object]:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def _write_source(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "source.json"
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return path


def test_generator_is_idempotent_and_preserves_published_base(tmp_path: Path):
    bundle_root = _copy_base(tmp_path)
    base_before = _tree_hash(bundle_root / "0.2.0")

    first = build_bundle(bundle_root=bundle_root, source_path=SOURCE)
    generated_before = _tree_hash(first.bundle_path)
    second = build_bundle(bundle_root=bundle_root, source_path=SOURCE)

    assert set(first.changed_files) == {*REQUIRED, "manifest.json"}
    assert second.changed_files == ()
    assert _tree_hash(second.bundle_path) == generated_before
    assert _tree_hash(bundle_root / "0.2.0") == base_before


def test_generator_emits_valid_hashes_counts_and_references(tmp_path: Path):
    bundle_root = _copy_base(tmp_path)
    result = build_bundle(bundle_root=bundle_root, source_path=SOURCE)

    loaded = load_bundle(result.bundle_path, strict=True)
    validated, compatibility, _trust = ContractValidator().validate(
        result.bundle_path, strict=True
    )
    manifest = loaded.manifest
    matchers = loaded.items("evidence_matchers.json")

    assert validated.manifest == manifest
    assert compatibility == "compatible_with_unknown_fields"
    assert manifest["knowledge_content_version"] == "0.2.1"
    assert manifest["artifact_sha256"] == result.artifact_sha256
    assert manifest["bundle_file_count"] == len(REQUIRED)
    assert manifest["claim_count"] == 541
    assert manifest["consumer_ready_platform_count"] == 3
    assert manifest["record_count"] == 635
    assert len(matchers) == 26
    assert sum("matcher_contract" in item for item in matchers) == 3
    assert any(item["id"] == "tuya_integration_status_problem" for item in matchers)
    for name in REQUIRED:
        if name not in {
            "applicability.json",
            "evidence_catalog.json",
            "evidence_matchers.json",
            "readiness.json",
        }:
            assert (result.bundle_path / name).read_bytes() == (
                bundle_root / "0.2.0" / name
            ).read_bytes()


@pytest.mark.parametrize("failure", ["duplicate", "unresolved", "invalid_matcher"])
def test_generator_fails_before_writing_invalid_bundle(
    tmp_path: Path, failure: str
):
    bundle_root = _copy_base(tmp_path)
    source = _source_copy(tmp_path)
    additions = source["additions"]
    assert isinstance(additions, dict)
    matchers = additions["evidence_matchers.json"]
    assert isinstance(matchers, list)

    if failure == "duplicate":
        duplicate = deepcopy(matchers[0])
        matchers.append(duplicate)
    elif failure == "unresolved":
        matcher = matchers[0]
        assert isinstance(matcher, dict)
        references = matcher["references"]
        assert isinstance(references, dict)
        references["observations"] = ["missing_observation"]
    else:
        matcher = matchers[0]
        assert isinstance(matcher, dict)
        contract = matcher["matcher_contract"]
        assert isinstance(contract, dict)
        contract["required_fields"] = []

    with pytest.raises(BundleBuildError):
        build_bundle(
            bundle_root=bundle_root,
            source_path=_write_source(tmp_path, source),
        )

    assert not (bundle_root / "0.2.1").exists()


def test_generator_check_mode_detects_stale_output(tmp_path: Path):
    bundle_root = _copy_base(tmp_path)
    with pytest.raises(BundleBuildError, match="stale"):
        build_bundle(bundle_root=bundle_root, source_path=SOURCE, check=True)

    build_bundle(bundle_root=bundle_root, source_path=SOURCE)
    checked = build_bundle(
        bundle_root=bundle_root,
        source_path=SOURCE,
        check=True,
    )
    assert checked.changed_files == ()


@pytest.mark.parametrize(
    "version",
    ("../escape", "0.2", "0.2.1/escape", "01.2.3", "v0.2.1"),
)
def test_generator_rejects_noncanonical_or_traversing_versions(
    tmp_path: Path, version: str
):
    bundle_root = _copy_base(tmp_path)
    with pytest.raises(BundleBuildError, match="semantic version"):
        build_bundle(
            version,
            bundle_root=bundle_root,
            source_path=SOURCE,
        )
    assert not (tmp_path / "escape").exists()
