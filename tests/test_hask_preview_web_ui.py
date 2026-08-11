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
    ):
        assert forbidden not in html
