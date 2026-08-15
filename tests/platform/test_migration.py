from pathlib import Path

from hadocs.platform.migration import MigrationManager
from hadocs.platform.paths import AppPaths, RuntimeMode


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
    assert len(result.messages) == 2
    assert "legacy configuration" in result.messages[0]
    assert "legacy device overrides" in result.messages[1]
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


def test_installed_migration_uses_executable_root_not_cwd(tmp_path: Path) -> None:
    install = tmp_path / "Program Files" / "HADocs"
    runtime = tmp_path / "LocalAppData" / "HADocs"
    resources = install / "_internal"
    (install / "config").mkdir(parents=True)
    (install / "config/config.json").write_text(
        '{"project_name": "RC3"}', encoding="utf-8"
    )
    paths = AppPaths(resources, runtime, RuntimeMode.WINDOWS_INSTALLED, install)

    result = MigrationManager(paths).migrate()

    assert result.migrated is True
    assert paths.config_file.read_text(encoding="utf-8") == '{"project_name": "RC3"}'
    assert (install / "config/config.json").exists()


def test_malformed_legacy_config_is_not_migrated(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.legacy_config_file.write_text("{broken", encoding="utf-8")

    result = MigrationManager(paths).migrate()

    assert result.migrated is False
    assert not paths.config_file.exists()


def test_existing_destination_wins_over_malformed_legacy(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    paths.config_dir.mkdir(parents=True)
    paths.config_file.write_text('{"project_name": "Current"}', encoding="utf-8")
    paths.legacy_config_file.write_text("{broken", encoding="utf-8")

    MigrationManager(paths).migrate()

    assert paths.config_file.read_text(encoding="utf-8") == '{"project_name": "Current"}'


def test_existing_local_app_data_database_is_untouched(tmp_path: Path) -> None:
    paths = AppPaths.discover(tmp_path)
    database = paths.config_dir / "hadocs.db"
    database.parent.mkdir(parents=True)
    original = b"operational-database-bytes"
    database.write_bytes(original)

    MigrationManager(paths).migrate()

    assert database.read_bytes() == original
