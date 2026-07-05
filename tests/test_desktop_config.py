from src.hadocs.gui.desktop_app import DesktopConfig, load_desktop_config, save_desktop_config


def test_desktop_config_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    config = DesktopConfig(
        home_assistant_url="http://ha.local:8123",
        token="secret",
        project_name="Test Home",
        output_dir="output",
        open_dashboard_after_scan=False,
        check_updates=True,
    )

    save_desktop_config(config, path)
    loaded = load_desktop_config(path)

    assert loaded.home_assistant_url == "http://ha.local:8123"
    assert loaded.token == "secret"
    assert loaded.project_name == "Test Home"
    assert loaded.open_dashboard_after_scan is False
    assert loaded.check_updates is True


def test_desktop_config_missing_file(tmp_path):
    loaded = load_desktop_config(tmp_path / "missing.json")
    assert loaded.project_name == "My Smart Home"
