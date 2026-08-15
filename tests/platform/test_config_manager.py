import json
import os
from pathlib import Path

import pytest

import hadocs.platform.config_manager as config_module
from hadocs.platform.config_manager import (
    DEFAULT_CONFIG,
    INSECURE_HTTP_WARNING,
    ConfigManager,
    ConfigPersistenceError,
    resolve_config_file,
)
from hadocs.platform.paths import AppPaths, RuntimePathError
from hadocs.runtime import RuntimeEnvironment


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
    monkeypatch.setattr(config_module, "get_home_assistant_token", lambda: None)
    monkeypatch.setattr(config_module, "set_home_assistant_token", lambda token: False)

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
    assert loaded["output_dir"] == str(tmp_path / DEFAULT_CONFIG["output_dir"])
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
    expected = dict(DEFAULT_CONFIG)
    expected["output_dir"] = str(tmp_path / "output")
    expected["cache_dir"] = str(tmp_path / "cache")
    assert manager.load() == expected


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


def test_relative_mutable_paths_resolve_against_data_root(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    resolved = manager.resolve_runtime_paths(
        {
            "output_dir": "reports",
            "cache_dir": "cache-data",
            "logs_dir": "logs-data",
            "hask_database_path": "config/operational.sqlite",
            "hask_bundle_path": "hadocs/knowledge/hask_bundle/0.2.1",
        }
    )

    assert resolved["output_dir"] == str((tmp_path / "reports").resolve())
    assert resolved["cache_dir"] == str((tmp_path / "cache-data").resolve())
    assert resolved["logs_dir"] == str((tmp_path / "logs-data").resolve())
    assert resolved["hask_database_path"] == str(
        (tmp_path / "config/operational.sqlite").resolve()
    )
    assert resolved["hask_bundle_path"] == str(
        (manager.paths.application_root / "hadocs/knowledge/hask_bundle/0.2.1").resolve()
    )


def test_relative_config_file_resolves_against_data_root(
    tmp_path: Path, monkeypatch
) -> None:
    paths = AppPaths.discover(tmp_path)
    monkeypatch.setenv("HADOCS_CONFIG_FILE", "alternate/config.json")

    assert resolve_config_file(paths) == (tmp_path / "alternate/config.json").resolve()


def test_relative_config_file_cannot_escape_data_root(
    tmp_path: Path, monkeypatch
) -> None:
    paths = AppPaths.discover(tmp_path)
    monkeypatch.setenv("HADOCS_CONFIG_FILE", "../config.json")

    with pytest.raises(RuntimePathError, match="configured root"):
        resolve_config_file(paths)


def test_absolute_config_and_mutable_paths_remain_supported(
    tmp_path: Path, monkeypatch
) -> None:
    paths = AppPaths.discover(tmp_path / "runtime")
    external_config = tmp_path / "external" / "config.json"
    external_output = tmp_path / "external" / "output"
    monkeypatch.setenv("HADOCS_CONFIG_FILE", str(external_config))

    assert resolve_config_file(paths) == external_config.resolve()
    resolved = ConfigManager(paths=paths).resolve_runtime_paths(
        {"output_dir": str(external_output)}
    )
    assert resolved["output_dir"] == str(external_output.resolve())


@pytest.mark.parametrize(
    "key",
    (
        "output_dir",
        "cache_dir",
        "logs_dir",
        "hask_database_path",
        "hask_database_credential_store_path",
        "hask_bundle_path",
    ),
)
def test_runtime_paths_cannot_escape_configured_roots(
    tmp_path: Path, key: str
) -> None:
    manager = make_manager(tmp_path)

    with pytest.raises(RuntimePathError, match="configured root"):
        manager.resolve_runtime_paths({key: "../escape"})


def test_save_validates_filesystem_before_new_credential(
    tmp_path: Path, monkeypatch
) -> None:
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("blocked", encoding="utf-8")
    manager = ConfigManager(config_file=parent_file / "config.json", paths=AppPaths.discover(tmp_path))
    credential_calls = []
    monkeypatch.setattr(config_module, "set_home_assistant_token", credential_calls.append)

    with pytest.raises(ConfigPersistenceError, match="could not save"):
        manager.save({"token": "do-not-display"})

    assert credential_calls == []


def test_replace_failure_rolls_back_only_new_credential(
    tmp_path: Path, monkeypatch
) -> None:
    manager = make_manager(tmp_path)
    actions = []
    monkeypatch.setattr(config_module, "get_home_assistant_token", lambda: None)
    monkeypatch.setattr(
        config_module,
        "set_home_assistant_token",
        lambda token: actions.append(("set", token)) or True,
    )
    monkeypatch.setattr(
        config_module,
        "delete_home_assistant_token",
        lambda: actions.append(("delete", None)) or True,
    )
    monkeypatch.setattr(os, "replace", lambda source, destination: (_ for _ in ()).throw(OSError("disk failure")))

    with pytest.raises(ConfigPersistenceError) as captured:
        manager.save({"token": "top-secret", "project_name": "Home"})

    assert actions == [("set", "top-secret"), ("delete", None)]
    assert "top-secret" not in str(captured.value)
    assert not manager.config_file.exists()


def test_existing_credential_with_missing_config_completes_setup(
    tmp_path: Path, monkeypatch
) -> None:
    manager = make_manager(tmp_path)
    writes = []
    monkeypatch.setattr(config_module, "get_home_assistant_token", lambda: "existing")
    monkeypatch.setattr(
        config_module,
        "set_home_assistant_token",
        lambda token: writes.append(token) or True,
    )

    manager.save({"token": "existing", "project_name": "Recovered"})

    assert writes == []
    assert json.loads(manager.config_file.read_text(encoding="utf-8")) == {
        "project_name": "Recovered"
    }


def test_atomic_save_replaces_existing_config_without_temp_files(
    tmp_path: Path, monkeypatch
) -> None:
    manager = make_manager(tmp_path)
    manager.config_file.parent.mkdir(parents=True)
    manager.config_file.write_text('{"project_name": "Old"}', encoding="utf-8")
    monkeypatch.setattr(config_module, "get_home_assistant_token", lambda: None)

    manager.save({"project_name": "New"})

    assert json.loads(manager.config_file.read_text(encoding="utf-8")) == {
        "project_name": "New"
    }
    assert list(manager.config_file.parent.glob("*.tmp")) == []
