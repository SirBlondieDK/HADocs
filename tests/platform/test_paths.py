from pathlib import Path

import pytest

import hadocs.platform.paths as paths_module
from hadocs.platform.paths import (
    INSTALLER_MARKER,
    AppPaths,
    RuntimeMode,
    RuntimePathError,
)


def _frozen_windows(monkeypatch, executable: Path, resources: Path) -> None:
    monkeypatch.setattr(paths_module.sys, "platform", "win32")
    monkeypatch.setattr(paths_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths_module.sys, "executable", str(executable))
    monkeypatch.setattr(paths_module.sys, "_MEIPASS", str(resources), raising=False)
    monkeypatch.delenv("HADOCS_ROOT", raising=False)


def test_discover_with_explicit_root(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    assert paths.root_dir == tmp_path.resolve()
    assert paths.data_root == tmp_path.resolve()
    assert paths.mode is RuntimeMode.EXPLICIT


def test_explicit_root_precedes_installed_marker(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "Program Files" / "HADocs" / "HADocs.exe"
    executable.parent.mkdir(parents=True)
    (executable.parent / INSTALLER_MARKER).write_text("installed", encoding="utf-8")
    _frozen_windows(monkeypatch, executable, tmp_path / "resources")
    override = tmp_path / "override"
    monkeypatch.setenv("HADOCS_ROOT", str(override))

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.EXPLICIT
    assert paths.data_root == override.resolve()


def test_installed_frozen_windows_ignores_program_files_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "Program Files" / "HADocs" / "HADocs.exe"
    executable.parent.mkdir(parents=True)
    (executable.parent / INSTALLER_MARKER).write_text("installed", encoding="utf-8")
    resources = executable.parent / "_internal"
    local_app_data = tmp_path / "profile" / "AppData" / "Local"
    readonly_cwd = tmp_path / "readonly-cwd"
    readonly_cwd.mkdir()
    _frozen_windows(monkeypatch, executable, resources)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.chdir(readonly_cwd)

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.WINDOWS_INSTALLED
    assert paths.data_root == local_app_data.resolve() / "HADocs"
    assert paths.application_root == resources.resolve()
    assert paths.config_file == local_app_data.resolve() / "HADocs/config/config.json"
    assert readonly_cwd not in paths.config_file.parents


def test_portable_frozen_windows_uses_executable_directory(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "portable" / "HADocs.exe"
    executable.parent.mkdir()
    _frozen_windows(monkeypatch, executable, executable.parent / "_internal")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.chdir(tmp_path)

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.WINDOWS_PORTABLE
    assert paths.data_root == executable.parent.resolve()


def test_installed_windows_requires_local_app_data(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "HADocs" / "HADocs.exe"
    executable.parent.mkdir()
    (executable.parent / INSTALLER_MARKER).touch()
    _frozen_windows(monkeypatch, executable, executable.parent / "_internal")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    with pytest.raises(RuntimePathError, match="LOCALAPPDATA"):
        AppPaths.discover()


def test_installed_windows_rejects_relative_local_app_data(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "HADocs" / "HADocs.exe"
    executable.parent.mkdir()
    (executable.parent / INSTALLER_MARKER).touch()
    _frozen_windows(monkeypatch, executable, executable.parent / "_internal")
    monkeypatch.setenv("LOCALAPPDATA", "relative-profile")

    with pytest.raises(RuntimePathError, match="absolute path"):
        AppPaths.discover()


def test_source_mode_preserves_repository_cwd(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "main.py").touch()
    (tmp_path / "pyproject.toml").touch()
    monkeypatch.setattr(paths_module.sys, "platform", "linux")
    monkeypatch.setattr(paths_module.sys, "frozen", False, raising=False)
    monkeypatch.delenv("HADOCS_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.SOURCE
    assert paths.application_root == tmp_path.resolve()
    assert paths.data_root == tmp_path.resolve()


def test_addon_config_file_does_not_move_the_data_root(
    tmp_path: Path, monkeypatch
) -> None:
    runtime = tmp_path / "addon-data"
    cwd = tmp_path / "app"
    cwd.mkdir()
    monkeypatch.setattr(paths_module.sys, "platform", "linux")
    monkeypatch.setattr(paths_module.sys, "frozen", False, raising=False)
    monkeypatch.delenv("HADOCS_ROOT", raising=False)
    monkeypatch.setenv("SUPERVISOR_TOKEN", "secret")
    monkeypatch.setenv("HADOCS_CONFIG_FILE", str(runtime / "config.json"))
    monkeypatch.chdir(cwd)

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.HOME_ASSISTANT_ADDON
    assert paths.data_root == cwd.resolve()


def test_container_config_file_does_not_move_the_data_root(
    tmp_path: Path, monkeypatch
) -> None:
    runtime = tmp_path / "container-config"
    cwd = tmp_path / "app"
    cwd.mkdir()
    monkeypatch.setattr(paths_module.sys, "platform", "linux")
    monkeypatch.setattr(paths_module.sys, "frozen", False, raising=False)
    monkeypatch.delenv("HADOCS_ROOT", raising=False)
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    monkeypatch.setenv("HADOCS_CONFIG_FILE", str(runtime / "config.json"))
    monkeypatch.chdir(cwd)

    paths = AppPaths.discover()

    assert paths.mode is RuntimeMode.CONTAINER
    assert paths.data_root == cwd.resolve()


def test_mutable_and_resource_paths_use_different_roots(tmp_path: Path) -> None:
    data = tmp_path / "data"
    resources = tmp_path / "resources"
    paths = AppPaths(resources, data, RuntimeMode.EXPLICIT, resources)

    assert paths.resolve_data_path("output/result") == (data / "output/result").resolve()
    assert paths.resolve_data_path("cache/raw") == (data / "cache/raw").resolve()
    assert paths.resolve_data_path("logs/app.log") == (data / "logs/app.log").resolve()
    assert paths.resolve_data_path("config/hadocs.db") == (data / "config/hadocs.db").resolve()
    assert paths.resolve_resource_path("hadocs/web/static") == (
        resources / "hadocs/web/static"
    ).resolve()


@pytest.mark.parametrize("relative", ("../escape", "nested/../../escape"))
def test_relative_paths_cannot_escape_their_roots(
    tmp_path: Path, relative: str
) -> None:
    data = tmp_path / "data"
    resources = tmp_path / "resources"
    paths = AppPaths(resources, data, RuntimeMode.EXPLICIT, resources)

    with pytest.raises(RuntimePathError, match="configured root"):
        paths.resolve_data_path(relative)
    with pytest.raises(RuntimePathError, match="configured root"):
        paths.resolve_resource_path(relative)


def test_explicit_absolute_paths_remain_supported(tmp_path: Path) -> None:
    data = tmp_path / "data"
    resources = tmp_path / "resources"
    external = tmp_path / "external" / "result.json"
    paths = AppPaths(resources, data, RuntimeMode.EXPLICIT, resources)

    assert paths.resolve_data_path(external) == external.resolve()
    assert paths.resolve_resource_path(external) == external.resolve()


def test_ensure_runtime_directories_creates_all_directories(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.ensure_runtime_directories()
    assert paths.config_dir.is_dir()
    assert paths.output_dir.is_dir()
    assert paths.cache_dir.is_dir()
    assert paths.logs_dir.is_dir()
