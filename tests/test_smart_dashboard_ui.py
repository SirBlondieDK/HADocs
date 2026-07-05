def test_smart_dashboard_imports():
    from src.hadocs.gui.app import App, load_logo_image, read_latest_summary, safe_read_json

    assert App is not None
    assert load_logo_image is not None
    assert read_latest_summary is not None
    assert safe_read_json is not None


def test_safe_read_json_missing(tmp_path):
    from src.hadocs.gui.app import safe_read_json

    assert safe_read_json(tmp_path / "missing.json") == {}
