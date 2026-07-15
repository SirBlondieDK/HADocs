from pathlib import Path

from src.hadocs.utils import config as config_module


def test_default_config_file_is_local_config_json():
    assert config_module.CONFIG_FILE.name == "config.json"


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("HADOCS_HA_URL", "http://homeassistant:8123")
    monkeypatch.setenv("HADOCS_TOKEN", "secret-token")
    monkeypatch.setenv("HADOCS_OUTPUT_DIR", "/output")
    monkeypatch.setenv("HADOCS_CACHE_DIR", "/cache")
    monkeypatch.setenv("HADOCS_PROJECT_NAME", "Docker Home")

    config = config_module.apply_environment_overrides({})

    assert config["ha_url"] == "http://homeassistant:8123"
    assert config["token"] == "secret-token"
    assert config["output_dir"] == "/output"
    assert config["cache_dir"] == "/cache"
    assert config["project_name"] == "Docker Home"


def test_empty_environment_values_do_not_override(monkeypatch):
    monkeypatch.setenv("HADOCS_OUTPUT_DIR", "")

    config = config_module.apply_environment_overrides(
        {"output_dir": "output"}
    )

    assert config["output_dir"] == "output"