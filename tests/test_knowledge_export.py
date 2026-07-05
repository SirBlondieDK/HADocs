from src.hadocs.knowledge.exporter import build_manifest, build_summary


def test_manifest_privacy_defaults():
    manifest = build_manifest()
    assert manifest["privacy"]["local_only"] is True
    assert manifest["privacy"]["telemetry"] is False
    assert manifest["privacy"]["ai_calls"] is False


def test_summary_empty():
    summary = build_summary()
    assert summary["project"] == "HADocs"
    assert summary["incident_count"] == 0
