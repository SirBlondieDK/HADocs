from __future__ import annotations

import json
from types import SimpleNamespace

from hadocs.web.api.hask_preview import (
    build_web_preview,
    load_latest_preview,
    sanitize_preview_payload,
)


def preview_payload() -> dict[str, object]:
    return {
        "feature_enabled": True,
        "hask_runtime_enabled": True,
        "bundle_available": True,
        "bundle_valid": True,
        "bundle_source": "packaged",
        "classification": "INSUFFICIENT_EVIDENCE",
        "validation_state": "valid",
        "compatibility_state": "compatible_with_unknown_fields",
        "contract_version": "1.1.0",
        "knowledge_content_version": "0.2.0",
        "knowledge_schema_version": "2.0.0",
        "checksum_prefix": "123456789abc",
        "coverage": [
            {"artifact": "platform_index", "item_count": 105},
            {"artifact": "evidence_catalog", "item_count": 731},
        ],
        "relevant_knowledge": [
            {
                "platform_id": "mqtt",
                "title": "MQTT",
                "summary": "Local broker knowledge.",
                "status": "reviewed",
            }
        ],
        "candidates": [],
        "matcher_readiness": [
            {
                "state": "BLOCKED",
                "matcher_id": "unifi_controller_connectivity_failure",
                "matcher_version": "1.0.0",
                "hask_record_ref": "unifi_controller_connection_state",
                "platform_scope": ["unifi"],
                "candidate_emitted": False,
                "missing_evidence_categories": [
                    "NATIVE_CONNECTION_RESULT",
                    "NATIVE_PROBLEM_SIGNAL",
                ],
                "rejection_codes": [],
            }
        ],
        "candidate_bridge_state": "READY",
        "candidate_bridge_rejection_code": None,
        "limitations": ["Authoritative API result deferred."],
        "notice": "Experimental preview.",
        "analytical_impact_statement": "No analytical impact.",
    }


def database_status() -> SimpleNamespace:
    return SimpleNamespace(
        enabled=True,
        identity_initialized=True,
        protected_backend="posix_file",
        protected_material_valid=True,
        database_file_present=True,
        schema_version=8,
        integrity_status="ok",
        foreign_key_status="ok",
        counts={
            "installations": 1,
            "scans": 3,
            "observations": 8,
            "entities": 1649,
            "relationships": 3220,
        },
        hask_enabled=True,
        candidate_bridge_enabled=True,
        native_domain_status_enabled=True,
        limitation="controller/API connection result deferred",
    )


def test_latest_scan_payload_is_preferred_and_fallback_is_lazy(tmp_path):
    path = tmp_path / "hask_preview.json"
    path.write_text(json.dumps(preview_payload()), encoding="utf-8")

    def forbidden_fallback():
        raise AssertionError("fallback must not run for a valid scan snapshot")

    payload, source = load_latest_preview(path, forbidden_fallback)

    assert source == "latest_scan"
    assert payload["relevant_knowledge"][0]["platform_id"] == "mqtt"


def test_protected_payload_fails_closed_to_live_status(tmp_path):
    persisted = preview_payload()
    persisted["persisted_scan_ref"] = 981
    path = tmp_path / "hask_preview.json"
    path.write_text(json.dumps(persisted), encoding="utf-8")

    payload, source = load_latest_preview(path, preview_payload)

    assert source == "live_status"
    assert "persisted_scan_ref" not in payload


def test_web_preview_exposes_only_redacted_status_and_derived_counts():
    safe = sanitize_preview_payload(preview_payload())
    assert safe is not None

    payload = build_web_preview(
        safe,
        source="latest_scan",
        database_status=database_status(),
    )

    assert payload["statistics"] == {
        "artifact_count": 2,
        "knowledge_record_count": 836,
        "relevant_platform_count": 1,
        "candidate_count": 0,
        "candidate_evaluation_count": 1,
        "candidate_classifications": {},
        "matcher_record_count": 0,
        "executable_matcher_count": 1,
        "matcher_readiness_states": {"BLOCKED": 1},
    }
    assert payload["operational_database"]["schema_version"] == 8
    assert payload["operational_database"]["counts"]["entities"] == 1649

    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "refh1_entity_",
        "persisted_scan_ref",
        "supporting_observation_ids",
        "supporting_relationship_ids",
        "entity_id",
        "device_id",
    ):
        assert forbidden not in encoded


def test_web_handler_uses_latest_scan_without_revalidating_bundle(
    tmp_path,
    monkeypatch,
):
    import hadocs.application.database_status as database_module
    import hadocs.web.app as web_app
    from hadocs.application.hask_preview import HaskPreviewService

    (tmp_path / "hask_preview.json").write_text(
        json.dumps(preview_payload()),
        encoding="utf-8",
    )

    monkeypatch.setattr(web_app, "OUTPUT_DIRECTORY", tmp_path)
    monkeypatch.setattr(web_app, "load_config", lambda: {})
    monkeypatch.setattr(
        database_module,
        "read_operational_database_status",
        lambda config: database_status(),
    )
    monkeypatch.setattr(
        HaskPreviewService,
        "snapshot",
        lambda self, config: (_ for _ in ()).throw(
            AssertionError("bundle must not be revalidated")
        ),
    )

    handler = object.__new__(web_app.HadocsRequestHandler)
    payload = handler._load_hask_preview()

    assert payload["preview_data_source"] == "latest_scan"
    assert payload["statistics"]["knowledge_record_count"] == 836
    assert payload["operational_database"]["integrity_status"] == "ok"


def test_candidate_bridge_diagnostics_survive_public_sanitization():
    source = preview_payload()
    source["candidate_bridge_state"] = "REJECTED"
    source["candidate_bridge_rejection_code"] = "BUNDLE_VALIDATION_FAILED"

    safe = sanitize_preview_payload(source)

    assert safe is not None
    assert safe["candidate_bridge_state"] == "REJECTED"
    assert (
        safe["candidate_bridge_rejection_code"]
        == "BUNDLE_VALIDATION_FAILED"
    )


def test_matcher_readiness_is_allowlisted_without_protected_identifiers():
    source = preview_payload()
    source["matcher_readiness"][0]["protected_subject_ref"] = (
        "refh1_entity_" + "c" * 64
    )
    source["matcher_readiness"][0]["persisted_scan_ref"] = 983

    assert sanitize_preview_payload(source) is None

    source = preview_payload()
    safe = sanitize_preview_payload(source)

    assert safe is not None
    assert safe["matcher_readiness"] == source["matcher_readiness"]
