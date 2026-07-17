import json
from pathlib import Path

import src.hadocs.platform.config_manager as config_module
from src.hadocs.platform.config_manager import (
    DEFAULT_CONFIG,
    INSECURE_HTTP_WARNING,
    ConfigManager,
)
from src.hadocs.platform.paths import AppPaths
from src.hadocs.runtime import RuntimeEnvironment


NON_ADDON_RUNTIME = object()


def make_manager(tmp_path: Path) -> ConfigManager:
    paths = AppPaths.discover(tmp_path)
    return ConfigManager(
        paths=paths,
        config_file=paths.config_file,
    )


def test_save_and_load_configuration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manager = make_manager(tmp_path)

    monkeypatch.delenv("HADOCS_HA_URL", raising=False)
    monkeypatch.delenv("HADOCS_TOKEN", raising=False)
    monkeypatch.delenv("HADOCS_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("HADOCS_CACHE_DIR", raising=False)
    monkeypatch.delenv("HADOCS_PROJECT_NAME", raising=False)
    monkeypatch.setattr(
        config_module,
        "detect_runtime",
        lambda: NON_ADDON_RUNTIME,
    )
    monkeypatch.setattr(
        config_module,
        "inject_token_into_runtime_config",
        lambda config: dict(config),
    )
    monkeypatch.setattr(
        config_module,
        "migrate_plaintext_token_from_config",
        lambda config: dict(config),
    )

    manager.save(
        {
            "ha_url": "https://ha.example",
            "project_name": "Test Home",
            "token": "must-not-be-written",
        }
    )

    stored = json.loads(manager.config_file.read_text(encoding="utf-8"))

    assert stored == {
        "ha_url": "https://ha.example",
        "project_name": "Test Home",
    }

    loaded = manager.load()

    assert loaded["ha_url"] == "https://ha.example"
    assert loaded["project_name"] == "Test Home"
    assert loaded["output_dir"] == DEFAULT_CONFIG["output_dir"]
    assert "token" not in loaded


def test_load_invalid_json_falls_back_to_defaults(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manager = make_manager(tmp_path)
    manager.config_file.parent.mkdir(parents=True)
    manager.config_file.write_text("{invalid", encoding="utf-8")

    monkeypatch.setattr(
        config_module,
        "detect_runtime",
        lambda: NON_ADDON_RUNTIME,
    )
    monkeypatch.setattr(
        config_module,
        "inject_token_into_runtime_config",
        lambda config: dict(config),
    )
    monkeypatch.setattr(
        config_module,
        "migrate_plaintext_token_from_config",
        lambda config: dict(config),
    )

    assert manager.load() == DEFAULT_CONFIG


def test_environment_overrides(monkeypatch, tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    monkeypatch.setenv("HADOCS_HA_URL", " https://env-ha.example ")
    monkeypatch.setenv("HADOCS_OUTPUT_DIR", " custom-output ")
    monkeypatch.setenv("HADOCS_CACHE_DIR", " custom-cache ")
    monkeypatch.setenv("HADOCS_PROJECT_NAME", " Environment Home ")
    monkeypatch.setenv("HADOCS_TOKEN", " secret-token ")

    result = manager.apply_environment_overrides({})

    assert result == {
        "ha_url": "https://env-ha.example",
        "output_dir": "custom-output",
        "cache_dir": "custom-cache",
        "project_name": "Environment Home",
        "token": "secret-token",
    }


def test_runtime_overrides_for_home_assistant_addon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)

    monkeypatch.setattr(
        config_module,
        "detect_runtime",
        lambda: RuntimeEnvironment.HOME_ASSISTANT_ADDON,
    )
    monkeypatch.setenv("SUPERVISOR_TOKEN", " supervisor-secret ")

    result = manager.apply_runtime_overrides(
        {
            "ha_url": "https://old.example",
            "token": "old-token",
        }
    )

    assert result["ha_url"] == "http://supervisor/core"
    assert result["token"] == "supervisor-secret"


def test_exists_with_environment_configuration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)

    monkeypatch.setattr(
        config_module,
        "detect_runtime",
        lambda: NON_ADDON_RUNTIME,
    )
    monkeypatch.setenv("HADOCS_HA_URL", "https://ha.example")
    monkeypatch.setenv("HADOCS_TOKEN", "token")

    assert manager.exists() is True


def test_exists_for_addon_requires_supervisor_token(
    monkeypatch,
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)

    monkeypatch.setattr(
        config_module,
        "detect_runtime",
        lambda: RuntimeEnvironment.HOME_ASSISTANT_ADDON,
    )
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)

    assert manager.exists() is False

    monkeypatch.setenv("SUPERVISOR_TOKEN", "token")

    assert manager.exists() is True


def test_validate_returns_blocking_problems(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    assert manager.validate({"ha_url": "", "token": ""}) == [
        "Home Assistant URL is missing.",
        "Token is missing.",
    ]

    assert manager.validate(
        {
            "ha_url": "homeassistant.local:8123",
            "token": "token",
        }
    ) == [
        "Home Assistant URL must start with http:// or https://.",
    ]


def test_validate_accepts_valid_configuration(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    assert manager.validate(
        {
            "ha_url": "https://ha.example",
            "token": "token",
        }
    ) == []


def test_validate_warnings_for_insecure_remote_http(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)

    warnings = manager.validate_warnings(
        {
            "ha_url": "http://192.168.1.10:8123",
            "token": "token",
        }
    )

    assert warnings == [INSECURE_HTTP_WARNING]


def test_validate_warnings_allows_internal_http_hosts(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)

    for host in ("localhost", "127.0.0.1", "[::1]", "supervisor"):
        warnings = manager.validate_warnings(
            {
                "ha_url": f"http://{host}:8123",
                "token": "token",
            }
        )

        assert warnings == []
