from pathlib import Path

import hadocs.runtime.detector as detector
from hadocs.runtime import RuntimeEnvironment


def test_home_assistant_addon_contract_has_highest_runtime_precedence(monkeypatch) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "secret")
    monkeypatch.setattr(detector.sys, "platform", "win32")

    assert detector.detect_runtime() is RuntimeEnvironment.HOME_ASSISTANT_ADDON


def test_container_contract_requires_hadocs_environment(tmp_path: Path, monkeypatch) -> None:
    marker = tmp_path / ".dockerenv"
    marker.touch()
    monkeypatch.setattr(detector, "_CONTAINER_MARKERS", (marker,))
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    monkeypatch.setenv("HADOCS_CONFIG_FILE", "/config/config.json")

    assert detector.detect_runtime() is RuntimeEnvironment.DOCKER


def test_windows_runtime_is_unchanged_without_addon_or_container(monkeypatch) -> None:
    monkeypatch.setattr(detector, "_CONTAINER_MARKERS", ())
    monkeypatch.setattr(detector.sys, "platform", "win32")
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    for name in (
        "HADOCS_HA_URL",
        "HADOCS_TOKEN",
        "HADOCS_CONFIG_FILE",
        "HADOCS_OUTPUT_DIR",
        "HADOCS_CACHE_DIR",
        "HADOCS_PROJECT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    assert detector.detect_runtime() is RuntimeEnvironment.WINDOWS
