from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from hadocs.application.database_status import (
    initialize_database_identity,
    read_operational_database_status,
)
from hadocs.application.operational_database import (
    DatabaseIdentityInitializationState,
)
from hadocs.cli.main import cmd_database_status
from hadocs.gui.dialogs.settings_dialog import SettingsDialog
from hadocs.hask_database import (
    CredentialStoreSecretProvider,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
)


ROOT = Path(__file__).resolve().parents[1]
FIXED_UUID = "123e4567-e89b-42d3-a456-426614174000"


class MemoryBackend:
    backend_kind = "windows_credential_manager"

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def write(self, handle: str, value: bytes) -> None:
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value) -> None:
        self.value = value


def provider() -> CredentialStoreSecretProvider:
    return CredentialStoreSecretProvider(
        MemoryBackend(), secret_factory=lambda length: b"\xa5" * length
    )


def base_config(path: Path) -> dict[str, object]:
    return {
        "hask_database_enabled": False,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "synthetic-windows-installation",
        "hask_enabled": False,
        "hask_candidate_evidence_enabled": False,
        "hask_native_integration_status_enabled": False,
    }


def initialize(path: Path):
    protected = provider()
    result, config = initialize_database_identity(
        base_config(path),
        secret_provider=protected,
        uuid_factory=lambda: FIXED_UUID,
    )
    assert result.state is DatabaseIdentityInitializationState.INITIALIZED
    return config, protected


def test_disabled_uninitialized_status_is_read_only_and_creates_nothing(tmp_path):
    path = tmp_path / "missing" / "operational.sqlite"
    parent = path.parent

    status = read_operational_database_status(base_config(path))

    assert status.enabled is False
    assert status.identity_initialized is False
    assert status.database_file_present is False
    assert status.schema_version is None
    assert not parent.exists()


def test_initialized_database_status_is_aggregate_and_redacted(tmp_path, capsys):
    path = tmp_path / "operational.sqlite"
    config, protected = initialize(path)
    service = HaskDatabaseService(
        HaskSQLiteConnectionFactory(
            HaskDatabaseConfig(
                enabled=True, path=path, expected_user_version=8
            )
        )
    )
    service.startup()
    service.shutdown()
    before = path.read_bytes()
    before_entries = sorted(item.name for item in tmp_path.iterdir())

    status = read_operational_database_status(
        config, secret_provider=protected
    )
    exit_code = cmd_database_status(
        config_loader=lambda: config, secret_provider=protected
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert status.identity_initialized is True
    assert status.protected_material_valid is True
    assert status.schema_version == 8
    assert status.integrity_status == "ok"
    assert status.foreign_key_status == "ok"
    assert status.counts == {
        "installations": 0,
        "scans": 0,
        "observations": 0,
        "entities": 0,
        "relationships": 0,
    }
    assert path.read_bytes() == before
    assert sorted(item.name for item in tmp_path.iterdir()) == before_entries
    for forbidden in (
        FIXED_UUID,
        config["hask_database_installation_scope"],
        config["hask_database_secret_handle"],
        "synthetic-windows-installation",
        str(path),
    ):
        assert str(forbidden) not in output


def test_status_handles_inaccessible_and_non_hadocs_files_safely(tmp_path):
    path = tmp_path / "not-a-database.sqlite"
    path.write_text("not sqlite", encoding="utf-8")

    status = read_operational_database_status(base_config(path))

    assert status.database_file_present is True
    assert status.schema_version is None
    assert status.integrity_status == "unavailable"
    assert all(value is None for value in status.counts.values())


def _dialog(config: dict[str, object]) -> SettingsDialog:
    dialog = SettingsDialog.__new__(SettingsDialog)
    dialog.cfg = dict(config)
    dialog.on_save = lambda updated: None
    dialog.database_enabled_var = Variable(config.get("hask_database_enabled", False))
    dialog.database_path_var = Variable(config.get("hask_database_path", ""))
    dialog.installation_ref_var = Variable(
        config.get("hask_database_installation_ref", "")
    )
    dialog.hask_enabled_var = Variable(config.get("hask_enabled", False))
    dialog.candidate_enabled_var = Variable(
        config.get("hask_candidate_evidence_enabled", False)
    )
    dialog.native_status_enabled_var = Variable(
        config.get("hask_native_integration_status_enabled", False)
    )
    dialog.database_status_var = Variable("")
    return dialog


def test_gui_initialization_requires_confirmation_and_does_not_enable(
    tmp_path, monkeypatch
):
    dialog = _dialog(base_config(tmp_path / "gui.sqlite"))
    calls = []
    monkeypatch.setattr(
        "hadocs.gui.dialogs.settings_dialog.messagebox.askyesno",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        "hadocs.application.database_status.initialize_database_identity",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    dialog.initialize_database_identity()

    assert calls == []
    assert dialog.database_enabled_var.get() is False


def test_gui_initialization_is_repeat_safe_and_uses_shared_service(
    tmp_path, monkeypatch
):
    config = base_config(tmp_path / "gui.sqlite")
    dialog = _dialog(config)
    updated = dict(config)
    updated["hask_database_identity_state"] = "initialized"
    calls = []
    monkeypatch.setattr(
        "hadocs.gui.dialogs.settings_dialog.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "hadocs.gui.dialogs.settings_dialog.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "hadocs.application.database_status.initialize_database_identity",
        lambda supplied, **kwargs: (
            calls.append((supplied, kwargs))
            or (
                SimpleNamespace(
                    state=DatabaseIdentityInitializationState.ALREADY_INITIALIZED
                ),
                updated,
            )
        ),
    )
    monkeypatch.setattr(
        "hadocs.utils.config.save_database_identity_config",
        lambda supplied: None,
    )
    monkeypatch.setattr(
        dialog, "refresh_database_status", lambda: calls.append("status")
    )

    dialog.initialize_database_identity()

    assert calls[0][0]["hask_database_enabled"] is False
    assert calls[-1] == "status"
    assert dialog.database_enabled_var.get() is False
    assert dialog.cfg["hask_database_enabled"] is False


def test_disabling_changes_only_flags_and_preserves_resources(tmp_path):
    path = tmp_path / "preserved.sqlite"
    path.write_bytes(b"preserved")
    config = base_config(path)
    config["hask_database_enabled"] = True
    config["hask_database_secret_handle"] = "opaque-handle"
    dialog = _dialog(config)
    dialog.database_enabled_var.set(False)

    updated = dialog._database_config()

    assert updated["hask_database_enabled"] is False
    assert updated["hask_database_secret_handle"] == "opaque-handle"
    assert path.read_bytes() == b"preserved"


def test_gui_opening_only_refreshes_status_and_binds_explicit_action():
    source = (
        ROOT / "src/hadocs/gui/dialogs/settings_dialog.py"
    ).read_text(encoding="utf-8")

    assert "command=self.initialize_database_identity" in source
    assert source.count("self.initialize_database_identity()") == 0
    assert "self.refresh_database_status()" in source
    assert "hadocs.application.database_status" in source


def test_cli_and_gui_status_use_the_same_application_service():
    cli = (ROOT / "src/hadocs/cli/main.py").read_text(encoding="utf-8")
    gui = (
        ROOT / "src/hadocs/gui/dialogs/settings_dialog.py"
    ).read_text(encoding="utf-8")

    service_import = "hadocs.application.database_status"
    assert service_import in cli
    assert service_import in gui
    assert "sqlite3" not in cli
    assert "sqlite3" not in gui


def test_pyinstaller_manifest_is_canonical_narrow_and_complete():
    spec = (ROOT / "installer/HADocs.spec").read_text(encoding="utf-8")
    migrations = sorted(
        (ROOT / "src/hadocs/hask_database/sql").glob("*.sql")
    )

    assert len(migrations) == 8
    assert 'pathex = [str(SRC)]' in spec
    assert '        "src",' not in spec
    assert '"hadocs.cli.main"' in spec
    assert '"hadocs.application.database_status"' in spec
    assert '"hadocs.metadata_collector"' in spec
    assert '"docs"' not in spec
    assert '"hudd.sqlite"' in spec
    assert '"masterlist.txt"' in spec
    assert '"schema.sql"' in spec
    assert 'console=True' in spec
