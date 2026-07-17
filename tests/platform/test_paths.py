from pathlib import Path

from src.hadocs.platform.paths import AppPaths


def test_discover_with_explicit_root(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)

    assert paths.root_dir == tmp_path.resolve()


def test_discover_uses_hadocs_root_environment_variable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HADOCS_ROOT", str(tmp_path))

    paths = AppPaths.discover()

    assert paths.root_dir == tmp_path.resolve()


def test_path_properties_are_resolved_from_root(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)

    assert paths.config_dir == tmp_path / "config"
    assert paths.output_dir == tmp_path / "output"
    assert paths.cache_dir == tmp_path / "cache"
    assert paths.logs_dir == tmp_path / "logs"
    assert paths.config_file == tmp_path / "config" / "config.json"
    assert paths.overrides_file == (
        tmp_path / "config" / "device_overrides.json"
    )
    assert paths.legacy_config_file == tmp_path / "config.json"
    assert paths.legacy_overrides_file == (
        tmp_path / "device_overrides.json"
    )


def test_ensure_runtime_directories_creates_all_directories(
    tmp_path: Path,
) -> None:
    paths = AppPaths.discover(tmp_path)

    paths.ensure_runtime_directories()

    assert paths.config_dir.is_dir()
    assert paths.output_dir.is_dir()
    assert paths.cache_dir.is_dir()
    assert paths.logs_dir.is_dir()
