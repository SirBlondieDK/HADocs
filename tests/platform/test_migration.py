from pathlib import Path

from src.hadocs.platform.migration import MigrationManager
from src.hadocs.platform.paths import AppPaths


def test_migrate_without_legacy_files_does_nothing(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)

    result = MigrationManager(paths).migrate()

    assert result.migrated is False
    assert result.messages == []
    assert paths.config_dir.is_dir()
    assert paths.output_dir.is_dir()
    assert paths.cache_dir.is_dir()
    assert paths.logs_dir.is_dir()


def test_migrate_copies_legacy_files_to_new_locations(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.legacy_config_file.write_text(
        '{"project_name": "Legacy"}',
        encoding="utf-8",
    )
    paths.legacy_overrides_file.write_text(
        '{"light.test": {"name": "Test"}}',
        encoding="utf-8",
    )

    result = MigrationManager(paths).migrate()

    assert result.migrated is True
    assert result.messages == [
        "Migrated config.json",
        "Migrated device_overrides.json",
    ]
    assert paths.config_file.read_text(encoding="utf-8") == (
        '{"project_name": "Legacy"}'
    )
    assert paths.overrides_file.read_text(encoding="utf-8") == (
        '{"light.test": {"name": "Test"}}'
    )

    # Version 1 keeps legacy files as a rollback-safe backup.
    assert paths.legacy_config_file.exists()
    assert paths.legacy_overrides_file.exists()


def test_migrate_does_not_overwrite_existing_destination(
    tmp_path: Path,
) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.config_dir.mkdir(parents=True)

    paths.legacy_config_file.write_text(
        '{"project_name": "Legacy"}',
        encoding="utf-8",
    )
    paths.config_file.write_text(
        '{"project_name": "Current"}',
        encoding="utf-8",
    )

    result = MigrationManager(paths).migrate()

    assert result.migrated is False
    assert result.messages == []
    assert paths.config_file.read_text(encoding="utf-8") == (
        '{"project_name": "Current"}'
    )


def test_migrate_is_idempotent(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.legacy_config_file.write_text("{}", encoding="utf-8")

    first_result = MigrationManager(paths).migrate()
    second_result = MigrationManager(paths).migrate()

    assert first_result.migrated is True
    assert second_result.migrated is False
    assert second_result.messages == []
