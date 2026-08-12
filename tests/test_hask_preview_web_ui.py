from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "src" / "hadocs" / "web" / "static" / "hask-preview.html"


def test_hask_preview_v2_exposes_the_public_preview_sections():
    html = PAGE.read_text(encoding="utf-8")

    for element_id in (
        'id="data-source"',
        'id="summary"',
        'id="status"',
        'id="database-status"',
        'id="database-counts"',
        'id="coverage"',
        'id="knowledge"',
        'id="readiness-summary"',
        'id="matcher-readiness"',
        'id="candidates"',
        'id="limitations"',
        'id="impact"',
    ):
        assert element_id in html

    for public_field in (
        "preview_data_source",
        "statistics",
        "operational_database",
        "relevant_knowledge",
        "matcher_readiness",
        "matcher_readiness_states",
        "executable_matcher_count",
        "candidate_bridge_state",
        "supporting_evidence_categories",
        "missing_evidence_categories",
    ):
        assert public_field in html


def test_hask_preview_v2_remains_ingress_relative_and_read_only():
    html = PAGE.read_text(encoding="utf-8")

    assert 'href="./"' in html
    assert 'new URL("api/hask-preview", document.baseURI)' in html
    assert 'method: "POST"' not in html
    assert 'target="_blank"' not in html
    assert "Experimental and read-only" in html


def test_hask_preview_v2_does_not_request_protected_identifiers():
    html = PAGE.read_text(encoding="utf-8")

    for forbidden in (
        "persisted_scan_ref",
        "supporting_observation_ids",
        "supporting_relationship_ids",
        "protected_subject_ref",
        "database_id",
        "entity_id",
        "device_id",
        "config_entry_id",
    ):
        assert forbidden not in html


def test_hask_preview_renders_candidate_matcher_readiness():
    html = PAGE.read_text(encoding="utf-8")

    for text in (
        "Matcher readiness",
        "Matcher records",
        "Executable matchers",
        "Candidate evaluations",
        "Supported candidates",
        "No match",
        "No executable matcher applies to the observed platform context; this does not establish that the integration is absent.",
        "Matchers completed, but no supported problem candidate was found.",
        "Matcher readiness is mixed; no supported candidate was emitted.",
        "Missing evidence",
        "Candidate emitted",
        "Bridge rejection",
        "renderMatcherReadiness",
    ):
        assert text in html
