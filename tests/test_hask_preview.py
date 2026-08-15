from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace

import pytest

from hadocs.application.hask_preview import (
    ANALYTICAL_IMPACT,
    HaskPreviewService,
    PREVIEW_NOTICE,
    PreviewClassification,
    render_hask_preview_html,
)
from hadocs.knowledge.hask_runtime.discovery import (
    BundleDiscovery,
    DiscoveryResult,
    packaged_bundle_path,
)
from hadocs.knowledge.hask_runtime.validation import VersionNegotiator
from hadocs.version import RELEASE_VERSION, __version__


ROOT = Path(__file__).resolve().parents[1]
PACKAGED = ROOT / "src" / "hadocs" / "knowledge" / "hask_bundle" / "0.2.1"


def config(**changes):
    value = {
        "hask_preview_enabled": True,
        "hask_enabled": True,
    }
    value.update(changes)
    return value


def copy_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "bundle"
    shutil.copytree(PACKAGED, target)
    return target


def rewrite_manifest(path: Path, update) -> None:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    update(manifest)
    (path / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.glob("*.json")):
        data = item.read_bytes()
        digest.update(item.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def candidate(
    classification: str,
    *,
    missing=(),
    rejection=None,
    matcher_id="matcher:public",
):
    return SimpleNamespace(
        classification=SimpleNamespace(value=classification),
        hask_record_ref="rca:public-record",
        matcher_id=matcher_id,
        matcher_version="1.0.0",
        persisted_scan_ref=981,
        protected_subject_ref="refh1_entity_" + "a" * 64,
        supporting_observation_ids=(12,),
        supporting_relationship_ids=(34,),
        missing_evidence_categories=tuple(missing),
        rejection_code=rejection,
    )


def test_hask_fully_disabled_and_packaged_bundle_is_only_detected() -> None:
    snapshot = HaskPreviewService().snapshot(
        {"hask_preview_enabled": False, "hask_enabled": False}
    )
    assert snapshot.classification is PreviewClassification.BUNDLE_DISABLED
    assert snapshot.bundle_available is True
    assert snapshot.bundle_valid is False
    assert snapshot.validation_state == "not_loaded"
    assert snapshot.coverage == ()


def test_explicit_valid_external_bundle_and_packaged_default(tmp_path: Path) -> None:
    external = copy_bundle(tmp_path)
    explicit = HaskPreviewService().snapshot(config(hask_bundle_path=str(external)))
    packaged = HaskPreviewService().snapshot(config())
    assert explicit.bundle_source == "configured"
    assert packaged.bundle_source == "packaged"
    assert explicit.bundle_valid and packaged.bundle_valid
    assert explicit.contract_version == packaged.contract_version == "1.1.0"


def test_explicit_missing_bundle_never_silently_falls_back(tmp_path: Path) -> None:
    snapshot = HaskPreviewService().snapshot(
        config(hask_bundle_path=str(tmp_path / "missing"))
    )
    assert snapshot.classification is PreviewClassification.BUNDLE_UNAVAILABLE
    assert snapshot.bundle_source == "configured"
    assert snapshot.bundle_available is False


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda path: (path / "manifest.json").write_text("{", encoding="utf-8"), "BUNDLE_INVALID"),
        (lambda path: (path / "platform_index.json").write_bytes(b"{}"), "BUNDLE_INVALID"),
        (lambda path: rewrite_manifest(path, lambda m: m.update(contract_version="2.0.0")), "BUNDLE_INVALID"),
        (lambda path: rewrite_manifest(path, lambda m: m.update(minimum_hadocs_version="99.0.0")), "BUNDLE_INVALID"),
    ],
)
def test_corrupt_checksum_contract_and_minimum_version_fail_closed(
    tmp_path: Path, mutation, expected: str
) -> None:
    bundle = copy_bundle(tmp_path)
    mutation(bundle)
    snapshot = HaskPreviewService().snapshot(config(hask_bundle_path=str(bundle)))
    assert snapshot.classification.value == expected
    assert snapshot.bundle_valid is False
    assert snapshot.candidates == ()


def test_version_authority_is_shared_by_runtime_and_package_metadata() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert RELEASE_VERSION == "0.17.0"
    assert __version__ == "0.17.0-rc3"
    assert VersionNegotiator.HADOCS_VERSION == RELEASE_VERSION
    assert 'dynamic = ["version"]' in pyproject
    assert 'version = {attr = "hadocs.version.__version__"}' in pyproject
    assert VersionNegotiator().validate_hadocs_version("0.17.0") == "hadocs_version_supported"


@dataclass
class EmptyBundle:
    manifest = {
        "contract_version": "1.1.0",
        "knowledge_content_version": "test",
        "knowledge_schema_version": "2.0.0",
        "artifact_sha256": "0" * 64,
    }
    artifacts = {"platform_index.json": {"items": []}}

    def items(self, name):
        return ()


class EmptyValidator:
    def validate(self, path, *, strict=True):
        return EmptyBundle(), "compatible_with_unknown_fields", "test"


def test_empty_coverage_is_explicit(tmp_path: Path) -> None:
    discovery = SimpleNamespace(
        discover=lambda configured: DiscoveryResult(tmp_path, "configured", "found")
    )
    snapshot = HaskPreviewService(
        discovery=discovery, validator=EmptyValidator()
    ).snapshot(config())
    assert [(item.artifact, item.item_count) for item in snapshot.coverage] == [
        ("platform_index", 0)
    ]


def test_validated_coverage_and_relevant_platform_knowledge() -> None:
    snapshot = HaskPreviewService().snapshot(
        config(), relevant_platforms=("unifi", "mikrotik", "not-present")
    )
    counts = {item.artifact: item.item_count for item in snapshot.coverage}
    assert counts["platform_index"] == 105
    assert counts["evidence_matchers"] == 26
    assert {item.platform_id for item in snapshot.relevant_knowledge} == {
        "unifi",
        "mikrotik",
    }


@pytest.mark.parametrize(
    ("classification", "missing", "rejection"),
    [
        ("SUPPORTED_CANDIDATE", (), None),
        ("INSUFFICIENT_EVIDENCE", ("CONTROLLER_API_RESULT",), None),
        ("NO_MATCH", (), None),
        ("NOT_APPLICABLE", (), None),
        ("REJECTED_CONFLICT", (), "CONTRADICTORY_EVIDENCE"),
    ],
)
def test_only_supported_candidates_are_emitted_as_candidate_insights(
    classification: str,
    missing: tuple[str, ...],
    rejection: str | None,
) -> None:
    result = SimpleNamespace(
        candidates=(
            candidate(
                classification,
                missing=missing,
                rejection=rejection,
            ),
        )
    )

    snapshot = HaskPreviewService().snapshot(
        config(),
        candidate_result=result,
    )

    if classification == "SUPPORTED_CANDIDATE":
        assert len(snapshot.candidates) == 1
        item = snapshot.candidates[0]
        assert (
            item.classification
            is PreviewClassification.SUPPORTED_CANDIDATE
        )
        assert item.explanation
    else:
        assert snapshot.candidates == ()

def test_preview_serialization_is_redacted_and_has_no_analytical_fields() -> None:
    result = SimpleNamespace(candidates=(candidate("SUPPORTED_CANDIDATE"),))
    raw = HaskPreviewService().snapshot(config(), candidate_result=result).canonical_bytes()
    forbidden = (
        b"refh1_entity_",
        b"persisted_scan_ref",
        b"supporting_observation_ids",
        b"supporting_relationship_ids",
        b"database_id",
        b"entity_id",
        b"device_id",
        b"config_entry_id",
        b"health_score",
        b"estimated_score_gain",
        b"http://",
        b"https://",
    )
    assert all(value not in raw for value in forbidden)
    assert b"validated observation" in raw


def test_tuya_candidate_explanation_preserves_cause_boundary() -> None:
    result = SimpleNamespace(candidates=(candidate(
        "SUPPORTED_CANDIDATE",
        matcher_id="tuya_integration_status_problem",
    ),))
    snapshot = HaskPreviewService().snapshot(config(), candidate_result=result)
    assert len(snapshot.candidates) == 1
    explanation = snapshot.candidates[0].explanation
    assert "Home Assistant reports a problem with the Tuya integration" in explanation
    assert "does not identify the underlying cause" in explanation
    assert "physical device" in explanation
    assert "Tuya Cloud" in explanation
    assert "user's network" in explanation


def test_html_preview_contains_notice_sections_and_no_protected_ids() -> None:
    result = SimpleNamespace(candidates=(candidate("INSUFFICIENT_EVIDENCE", missing=("API_RESULT",)),))
    html = render_hask_preview_html(
        HaskPreviewService().snapshot(config(), candidate_result=result)
    )
    for heading in (
        "HASK Preview",
        "Knowledge coverage",
        "Relevant knowledge",
        "Candidate insights",
        "Conflicts and limitations",
        "Analytical impact",
        "Enablement",
    ):
        assert heading in html
    assert PREVIEW_NOTICE in html
    assert "refh1_entity_" not in html


def test_web_route_and_overview_card_render_the_preview(monkeypatch) -> None:
    from hadocs.web.app import HadocsRequestHandler

    handler = object.__new__(HadocsRequestHandler)
    served = []
    monkeypatch.setattr(handler, "_request_path", lambda: "/hask-preview")
    monkeypatch.setattr(handler, "_serve_web_file", served.append)
    handler.do_GET()
    assert served == ["hask-preview.html"]
    index = (ROOT / "src/hadocs/web/static/index.html").read_text(encoding="utf-8")
    page = (ROOT / "src/hadocs/web/static/hask-preview.html").read_text(encoding="utf-8")
    assert "HASK Preview" in index and "Experimental · no score impact" in index
    assert "api/hask-preview" in page


def test_bundle_tree_is_immutable_and_restart_stable() -> None:
    before = tree_hash(PACKAGED)
    first = HaskPreviewService().snapshot(config(), relevant_platforms=("unifi",))
    second = HaskPreviewService().snapshot(config(), relevant_platforms=("unifi",))
    assert first.canonical_bytes() == second.canonical_bytes()
    assert tree_hash(PACKAGED) == before


def test_preview_does_not_mutate_or_carry_normal_analytics() -> None:
    analytical = {
        "findings": ["f1"],
        "incidents": ["i1"],
        "root_causes": ["r1"],
        "recommendations": ["a1"],
        "severity": "warning",
        "affected_entities": ["synthetic.one"],
        "health_score": 82,
        "potential_health_score": 88,
        "estimated_score_gain": 6,
        "device_classifications": ["online"],
        "report_analytical_dtos": {"stable": True},
    }
    baseline = deepcopy(analytical)
    disabled = HaskPreviewService().snapshot(
        {"hask_preview_enabled": False, "hask_enabled": False}
    )
    active = HaskPreviewService().snapshot(config())
    assert analytical == baseline
    assert disabled.analytical_impact_statement == active.analytical_impact_statement == ANALYTICAL_IMPACT
    assert set(analytical).isdisjoint(active.as_dict())


def test_generated_report_analytics_are_identical_when_preview_changes(
    tmp_path: Path,
) -> None:
    from hadocs.reports.generator import generate_executive_dashboard

    model = SimpleNamespace(
        areas={}, devices={}, entities={}, integrations={}
    )
    executive = SimpleNamespace(
        score=100,
        potential_score=100,
        estimated_repair_minutes=0,
        main_cause="No major root cause",
        actions=(),
    )
    disabled = HaskPreviewService().snapshot(
        {"hask_preview_enabled": False, "hask_enabled": False}
    )
    active = HaskPreviewService().snapshot(config())
    left, right = tmp_path / "disabled", tmp_path / "active"
    arguments = (
        "Synthetic Home",
        model,
        executive,
        (),
        None,
        {},
        (),
        (),
        "2026-07-30",
    )
    generate_executive_dashboard(left, *arguments, hask_preview=disabled)
    generate_executive_dashboard(right, *arguments, hask_preview=active)
    left_html = (left / "index.html").read_text(encoding="utf-8")
    right_html = (right / "index.html").read_text(encoding="utf-8")
    pattern = re.compile(
        r'<section class="section panel hask-preview" id="hask-preview">.*?</section>',
        re.DOTALL,
    )
    assert pattern.sub("<HASK_PREVIEW>", left_html) == pattern.sub(
        "<HASK_PREVIEW>", right_html
    )
    assert PREVIEW_NOTICE in left_html and PREVIEW_NOTICE in right_html


def test_home_assistant_app_preview_is_explicit_and_default_disabled() -> None:
    addon = (ROOT / "hadocs/config.yaml").read_text(encoding="utf-8")
    run = (ROOT / "hadocs/run.sh").read_text(encoding="utf-8")
    assert "hask_preview_enabled: false" in addon
    assert "hask_preview_enabled: bool" in addon
    assert "HADOCS_HASK_PREVIEW_ENABLED" in run
    assert "HASK_PREVIEW_ENABLED" in run


def test_packaged_resource_discovery_is_source_and_frozen_safe() -> None:
    discovered = BundleDiscovery().discover()
    assert packaged_bundle_path() == PACKAGED
    assert discovered.path == PACKAGED
    assert discovered.source == "packaged"
    spec = (ROOT / "installer/HADocs.spec").read_text(encoding="utf-8")
    assert "hask_bundle" in spec
    assert "hadocs.application.hask_preview" in spec


def test_cli_preview_uses_the_shared_redacted_model(capsys) -> None:
    from hadocs.cli.main import cmd_hask_preview

    assert cmd_hask_preview(
        config_loader=lambda: {
            "hask_preview_enabled": False,
            "hask_enabled": False,
        }
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["classification"] == "BUNDLE_DISABLED"
    assert payload["analytical_impact_statement"] == ANALYTICAL_IMPACT


def test_issue_29_shared_eligibility_remains_the_only_disabled_predicate() -> None:
    from hadocs.core.entity_eligibility import is_disabled_entity
    from hadocs.core.models import EntityModel

    entity = EntityModel(
        entity_id="sensor.synthetic_disabled",
        name="Synthetic disabled",
        domain="sensor",
        platform="systemmonitor",
        device_id=None,
        area_id=None,
        state="unknown",
        attributes={},
        is_ignored=False,
        is_physical=False,
        registry={"disabled_by": "user"},
        raw={"disabled_by": "user"},
    )
    assert is_disabled_entity(entity) is True
    assert "is_disabled_entity" in inspect.getsource(is_disabled_entity)


def test_candidate_bridge_rejection_is_public_but_protected_data_is_not():
    result = SimpleNamespace(
        state=SimpleNamespace(value="REJECTED"),
        rejection_code="BUNDLE_VALIDATION_FAILED",
        candidates=(),
    )

    snapshot = HaskPreviewService().snapshot(config(), candidate_result=result)

    assert snapshot.candidate_bridge_state == "REJECTED"
    assert (
        snapshot.candidate_bridge_rejection_code
        == "BUNDLE_VALIDATION_FAILED"
    )
    raw = snapshot.canonical_bytes()
    assert b"BUNDLE_VALIDATION_FAILED" in raw
    assert b"persisted_scan_ref" not in raw
    assert b"refh1_entity_" not in raw


def test_duplicate_entity_candidate_insights_are_collapsed():
    duplicated = candidate("SUPPORTED_CANDIDATE")
    result = SimpleNamespace(
        state=SimpleNamespace(value="READY"),
        rejection_code=None,
        candidates=(duplicated, duplicated),
    )

    snapshot = HaskPreviewService().snapshot(config(), candidate_result=result)

    assert snapshot.candidate_bridge_state == "READY"
    assert len(snapshot.candidates) == 1


def test_matcher_readiness_is_redacted_and_preserved():
    readiness = SimpleNamespace(
        state=SimpleNamespace(value="BLOCKED"),
        matcher_id="unifi_controller_connectivity_failure",
        matcher_version="1.0.0",
        hask_record_ref="unifi_controller_connection_state",
        platform_scope=("unifi",),
        candidate_emitted=False,
        missing_evidence_categories=(
            "NATIVE_CONNECTION_RESULT",
            "NATIVE_PROBLEM_SIGNAL",
        ),
        rejection_codes=(),
        protected_subject_ref="refh1_entity_" + "b" * 64,
        persisted_scan_ref=982,
    )
    result = SimpleNamespace(
        state=SimpleNamespace(value="READY"),
        rejection_code=None,
        candidates=(),
        matcher_readiness=(readiness,),
    )

    snapshot = HaskPreviewService().snapshot(
        config(),
        candidate_result=result,
    )

    assert len(snapshot.matcher_readiness) == 1
    item = snapshot.matcher_readiness[0]
    assert item.state == "BLOCKED"
    assert item.platform_scope == ("unifi",)
    assert item.candidate_emitted is False
    assert item.missing_evidence_categories == (
        "NATIVE_CONNECTION_RESULT",
        "NATIVE_PROBLEM_SIGNAL",
    )

    raw = snapshot.canonical_bytes()
    assert b"unifi_controller_connectivity_failure" in raw
    assert b"refh1_entity_" not in raw
    assert b"persisted_scan_ref" not in raw


def test_preview_classification_comes_from_matcher_readiness():
    def readiness(state: str):
        return SimpleNamespace(
            state=SimpleNamespace(value=state),
            matcher_id=f"matcher_{state.casefold()}",
            matcher_version="1.0.0",
            hask_record_ref=f"record_{state.casefold()}",
            platform_scope=("synthetic",),
            candidate_emitted=False,
            missing_evidence_categories=(),
            rejection_codes=(),
        )

    not_applicable = SimpleNamespace(
        state=SimpleNamespace(value="READY"),
        rejection_code=None,
        candidates=(),
        matcher_readiness=(readiness("NOT_APPLICABLE"),),
    )
    blocked = SimpleNamespace(
        state=SimpleNamespace(value="READY"),
        rejection_code=None,
        candidates=(),
        matcher_readiness=(
            readiness("NOT_APPLICABLE"),
            readiness("BLOCKED"),
        ),
    )
    no_match = SimpleNamespace(
        state=SimpleNamespace(value="READY"),
        rejection_code=None,
        candidates=(),
        matcher_readiness=(
            readiness("NOT_APPLICABLE"),
            readiness("NO_MATCH"),
        ),
    )

    assert (
        HaskPreviewService()
        .snapshot(config(), candidate_result=not_applicable)
        .classification
        is PreviewClassification.NOT_APPLICABLE
    )
    assert (
        HaskPreviewService()
        .snapshot(config(), candidate_result=blocked)
        .classification
        is PreviewClassification.INSUFFICIENT_EVIDENCE
    )
    assert (
        HaskPreviewService()
        .snapshot(config(), candidate_result=no_match)
        .classification
        is PreviewClassification.NO_MATCH
    )
