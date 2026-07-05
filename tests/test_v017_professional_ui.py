def test_v017_ui_imports():
    from src.hadocs.gui.app import (
        App,
        AboutDialog,
        FirstRunWizard,
        HealthGauge,
        SettingsDialog,
        Theme,
        app_path,
        load_logo_image,
        read_latest_summary,
        safe_read_json,
    )

    assert App is not None
    assert AboutDialog is not None
    assert FirstRunWizard is not None
    assert HealthGauge is not None
    assert SettingsDialog is not None
    assert Theme is not None
    assert app_path is not None
    assert load_logo_image is not None
    assert read_latest_summary is not None
    assert safe_read_json is not None


def test_safe_read_json_valid(tmp_path):
    from src.hadocs.gui.app import safe_read_json

    path = tmp_path / "data.json"
    path.write_text('{"ok": true}', encoding="utf-8")
    assert safe_read_json(path) == {"ok": True}
