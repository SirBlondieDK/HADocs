from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest
import yaml

from hadocs.cli.main import cmd_database_init
from hadocs.hask_database import CredentialStoreSecretProvider
from hadocs.platform.config_manager import ConfigManager, DEFAULT_CONFIG


ROOT = Path(__file__).resolve().parents[1]


class MemoryBackend:
    backend_kind = "windows_credential_manager"

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.writes = 0

    def write(self, handle: str, value: bytes) -> None:
        self.writes += 1
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


def _addon_configuration() -> dict[str, object]:
    return yaml.safe_load(
        (ROOT / "hadocs/config.yaml").read_text(encoding="utf-8")
    )


def _run_option_adapter(
    tmp_path: Path, options: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    script = (ROOT / "hadocs/run.sh").read_text(encoding="utf-8")
    marker = "python - <<'PY'\n"
    start = script.index(marker) + len(marker)
    source = script[start:script.index("\nPY\n", start)]
    options_file = tmp_path / "options.json"
    options_file.write_text(json.dumps(options), encoding="utf-8")
    source = source.replace(
        'path = Path("/data/options.json")',
        f"path = Path({str(options_file)!r})",
    )
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_addon_and_application_defaults_keep_every_feature_disabled() -> None:
    configuration = _addon_configuration()
    options = configuration["options"]
    schema = configuration["schema"]
    disabled = (
        "hask_database_initialize",
        "hask_database_enabled",
        "hask_enabled",
        "hask_candidate_evidence_enabled",
        "hask_native_integration_status_enabled",
    )

    assert all(options[name] is False for name in disabled)
    assert all(schema[name] == "bool" for name in disabled)
    assert DEFAULT_CONFIG["hask_database_enabled"] is False
    assert DEFAULT_CONFIG["hask_enabled"] is False
    assert DEFAULT_CONFIG["hask_candidate_evidence_enabled"] is False
    assert DEFAULT_CONFIG["hask_native_integration_status_enabled"] is False


def test_addon_uses_persistent_paths_and_real_runtime_names() -> None:
    configuration = _addon_configuration()
    options = configuration["options"]
    script = (ROOT / "hadocs/run.sh").read_text(encoding="utf-8")

    assert options["hask_database_path"] == "/config/hadocs.db"
    assert options["hask_bundle_path"] == "/config/hask-bundle"
    assert '/config/.hadocs/credentials' in script
    assert "HADOCS_HASK_DATABASE_PATH" in script
    assert "HADOCS_HASK_DATABASE_ENABLED" in script
    assert "HADOCS_HASK_DATABASE_SECRET_BACKEND" in script
    assert "HADOCS_HASK_CANDIDATE_EVIDENCE_ENABLED" in script
    assert "HADOCS_HASK_NATIVE_INTEGRATION_STATUS_ENABLED" in script
    assert "HADOCS_DATABASE_FILE" not in script


def test_addon_mapping_and_image_use_the_packaged_cli_startup() -> None:
    configuration = _addon_configuration()
    mappings = {
        item["type"]: item["read_only"] for item in configuration["map"]
    }
    addon_dockerfile = (ROOT / "hadocs/Dockerfile").read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert mappings["addon_config"] is False
    assert 'COPY run.sh /run.sh' in addon_dockerfile
    assert 'CMD ["/run.sh"]' in addon_dockerfile
    assert project["project"]["scripts"]["hadocs"] == "hadocs.cli.main:main"


def test_addon_initializes_only_on_explicit_request_before_web_start() -> None:
    script = (ROOT / "hadocs/run.sh").read_text(encoding="utf-8")

    condition = 'if [ "${DATABASE_INITIALIZE}" = "true" ]; then'
    assert script.count("hadocs database init") == 1
    assert script.index(condition) < script.index("hadocs database init")
    assert script.index("hadocs database init") < script.index(
        "exec python -m hadocs.web.app"
    )
    assert 'if [ "${DATABASE_ENABLED}" = "true" ]' not in script


def test_addon_option_adapter_keeps_initialization_and_enablement_independent(
    tmp_path: Path,
) -> None:
    completed = _run_option_adapter(
        tmp_path,
        {
            "hask_database_initialize": True,
            "hask_database_enabled": False,
            "hask_database_path": "/config/operational.sqlite",
            "hask_database_installation_ref": "synthetic-addon",
            "hask_enabled": False,
            "hask_candidate_evidence_enabled": False,
            "hask_native_integration_status_enabled": False,
        },
    )

    assert completed.returncode == 0, completed.stderr
    assignments = dict(
        line.split("=", 1) for line in completed.stdout.splitlines()
    )
    assert assignments["DATABASE_INITIALIZE"] == "true"
    assert assignments["DATABASE_ENABLED"] == "false"
    assert assignments["DATABASE_PATH"] == "/config/operational.sqlite"
    assert assignments["DATABASE_INSTALLATION_REF"] == "synthetic-addon"
    assert assignments["HASK_ENABLED"] == "false"
    assert assignments["HASK_CANDIDATE_EVIDENCE_ENABLED"] == "false"
    assert assignments["HASK_NATIVE_INTEGRATION_STATUS_ENABLED"] == "false"


def test_addon_option_adapter_rejects_nonpersistent_database_path(
    tmp_path: Path,
) -> None:
    completed = _run_option_adapter(
        tmp_path,
        {"hask_database_path": "/tmp/operational.sqlite"},
    )

    assert completed.returncode != 0
    assert "must be under /config" in completed.stderr
    assert "/tmp/operational.sqlite" not in completed.stderr


def test_app_environment_adapter_maps_text_and_strict_booleans(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manager = ConfigManager(config_file=tmp_path / "config.json")
    monkeypatch.setenv("HADOCS_HASK_DATABASE_ENABLED", " true ")
    monkeypatch.setenv("HADOCS_HASK_DATABASE_PATH", " /config/hadocs.db ")
    monkeypatch.setenv(
        "HADOCS_HASK_DATABASE_INSTALLATION_REF", " home-assistant-app "
    )
    monkeypatch.setenv("HADOCS_HASK_DATABASE_SECRET_BACKEND", " posix_file ")
    monkeypatch.setenv(
        "HADOCS_HASK_CREDENTIAL_STORE_PATH",
        " /config/.hadocs/credentials ",
    )
    monkeypatch.setenv("HADOCS_HASK_ENABLED", "false")
    monkeypatch.setenv("HADOCS_HASK_BUNDLE_PATH", " /config/hask-bundle ")
    monkeypatch.setenv("HADOCS_HASK_CANDIDATE_EVIDENCE_ENABLED", "0")
    monkeypatch.setenv("HADOCS_HASK_NATIVE_INTEGRATION_STATUS_ENABLED", "on")

    result = manager.apply_environment_overrides({})

    assert result == {
        "hask_database_enabled": True,
        "hask_database_path": "/config/hadocs.db",
        "hask_database_installation_ref": "home-assistant-app",
        "hask_database_secret_backend": "posix_file",
        "hask_database_credential_store_path": "/config/.hadocs/credentials",
        "hask_enabled": False,
        "hask_bundle_path": "/config/hask-bundle",
        "hask_candidate_evidence_enabled": False,
        "hask_native_integration_status_enabled": True,
    }


def test_app_environment_adapter_rejects_ambiguous_boolean(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manager = ConfigManager(config_file=tmp_path / "config.json")
    monkeypatch.setenv("HADOCS_HASK_DATABASE_ENABLED", "sometimes")

    with pytest.raises(ValueError, match="HADOCS_HASK_DATABASE_ENABLED"):
        manager.apply_environment_overrides({})


def test_initialization_is_repeat_safe_and_independent_from_enablement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manager = ConfigManager(config_file=tmp_path / "config.json")
    monkeypatch.setenv("HADOCS_HASK_DATABASE_ENABLED", "false")
    monkeypatch.setenv(
        "HADOCS_HASK_DATABASE_PATH", str(tmp_path / "operational.sqlite")
    )
    monkeypatch.setenv(
        "HADOCS_HASK_DATABASE_INSTALLATION_REF", "synthetic-addon"
    )
    state = manager.apply_environment_overrides(DEFAULT_CONFIG)
    backend = MemoryBackend()
    provider = CredentialStoreSecretProvider(
        backend,
        secret_factory=lambda length: b"\xa6" * length,
    )

    def load() -> dict[str, object]:
        return dict(state)

    def save(value: dict[str, object]) -> None:
        state.clear()
        state.update(value)

    assert cmd_database_init(
        config_loader=load,
        config_saver=save,
        secret_provider=provider,
    ) == 0
    first_identity = {
        name: state[name]
        for name in (
            "hask_database_installation_uuid",
            "hask_database_installation_scope",
            "hask_database_secret_handle",
            "hask_database_secret_generation",
        )
    }
    assert state["hask_database_enabled"] is False
    assert backend.writes == 1
    assert tuple(backend.values.values()) == (b"\xa6" * 32,)

    assert cmd_database_init(
        config_loader=load,
        config_saver=save,
        secret_provider=provider,
    ) == 0
    assert {name: state[name] for name in first_identity} == first_identity
    assert backend.writes == 1
    assert "already initialized" in capsys.readouterr().out

    monkeypatch.setenv("HADOCS_HASK_DATABASE_ENABLED", "true")
    enabled = manager.apply_environment_overrides(state)
    assert enabled["hask_database_enabled"] is True
    monkeypatch.setenv("HADOCS_HASK_DATABASE_ENABLED", "false")
    disabled = manager.apply_environment_overrides(enabled)
    assert disabled["hask_database_enabled"] is False
    assert {name: disabled[name] for name in first_identity} == first_identity
    assert backend.writes == 1


def test_canonical_documentation_uses_only_the_real_database_command() -> None:
    document = (
        ROOT / "docs/integration/HASK_INTEGRATION_STATUS.md"
    ).read_text(encoding="utf-8")
    cli = (ROOT / "src/hadocs/cli/main.py").read_text(encoding="utf-8")

    assert "hadocs database init" in document
    assert "hadocs database status" in document
    assert 'database_sub.add_parser(\n        "init"' in cli
    assert 'database_sub.add_parser(\n        "status"' in cli
    for name in (
        "hask_database_enabled",
        "hask_enabled",
        "hask_candidate_evidence_enabled",
        "hask_native_integration_status_enabled",
    ):
        assert f"`{name}`" in document
