from __future__ import annotations

import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sqlite3

import pytest

from hadocs.application.operational_database import (
    DatabaseIdentityInitializationState,
    OperationalDatabaseOperation,
    initialize_operational_database_identity,
    persist_operational_database,
)
from hadocs.cli.main import cmd_database_init
from hadocs.core.models import InstallationModel
from hadocs.hask_database import (
    CredentialStoreBackend,
    CredentialStoreSecretProvider,
    HaskDatabaseApplicationConfig,
    HaskDatabaseConfig,
    HaskDatabaseService,
    HaskSQLiteConnectionFactory,
    NullSecretProvider,
    ObservationInput,
    OperationalSliceRequest,
    RecoveryModeError,
    SecretUnavailableError,
    derive_installation_scope,
    schema_sha256,
    select_secret_provider,
    WINDOWS_CREDENTIAL_BACKEND,
)


FROZEN_SCHEMA_SHA256 = (
    "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"
)
FIXED_UUID = "123e4567-e89b-42d3-a456-426614174000"
FIXED_SCOPE = "is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194"


class MemoryBackend:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.writes = 0
        self.reads = 0
        self.deletes = 0
        self.read_error: Exception | None = None

    def write(self, handle: str, value: bytes) -> None:
        self.writes += 1
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        self.reads += 1
        if self.read_error is not None:
            raise self.read_error
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        self.deletes += 1
        return self.values.pop(handle, None) is not None


def base_config(path: Path) -> dict[str, object]:
    return {
        "hask_database_path": str(path),
        "hask_database_installation_ref": "synthetic-identity-installation",
    }


def initialized(
    path: Path,
    *,
    secret: bytes = b"\xa7" * 32,
) -> tuple[dict[str, object], MemoryBackend, CredentialStoreSecretProvider]:
    backend = MemoryBackend()
    provider = CredentialStoreSecretProvider(
        backend, secret_factory=lambda length: secret if length == 32 else b""
    )
    result, config = initialize_operational_database_identity(
        base_config(path),
        secret_provider=provider,
        uuid_factory=lambda: FIXED_UUID,
    )
    assert result.state is DatabaseIdentityInitializationState.INITIALIZED
    config["hask_database_enabled"] = True
    return config, backend, provider


def empty_model() -> InstallationModel:
    return InstallationModel(
        areas={},
        devices={},
        entities={},
        integrations={},
        config={},
        states=[],
        services=[],
        labels=[],
        raw={},
    )


def operation() -> OperationalDatabaseOperation:
    return OperationalDatabaseOperation(
        identity="identity-foundation-operation",
        started_at="2026-07-27T14:00:00Z",
        terminal_at="2026-07-27T14:00:01Z",
    )


def test_scope_derivation_matches_frozen_vector_and_grammar():
    assert derive_installation_scope(FIXED_UUID) == FIXED_SCOPE
    assert re.fullmatch(r"is1_[0-9a-f]{64}", FIXED_SCOPE)


def test_windows_backend_identity_contract_remains_compatible():
    backend = CredentialStoreBackend()
    provider = CredentialStoreSecretProvider(backend)

    assert backend.backend_kind == WINDOWS_CREDENTIAL_BACKEND
    assert provider.backend_kind == WINDOWS_CREDENTIAL_BACKEND


def test_windows_backend_adapter_retains_binary_credential_calls(monkeypatch):
    from hadocs.security import credential_store as store_module

    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        store_module,
        "set_protected_binary_credential",
        lambda handle, value: calls.append(("write", handle, value)),
    )
    monkeypatch.setattr(
        store_module,
        "get_protected_binary_credential",
        lambda handle: calls.append(("read", handle)) or b"x" * 32,
    )
    monkeypatch.setattr(
        store_module,
        "delete_protected_binary_credential",
        lambda handle: calls.append(("delete", handle)) or True,
    )
    backend = CredentialStoreBackend()

    backend.write("opaque-handle", b"x" * 32)
    assert backend.read("opaque-handle") == b"x" * 32
    assert backend.delete("opaque-handle") is True
    assert calls == [
        ("write", "opaque-handle", b"x" * 32),
        ("read", "opaque-handle"),
        ("delete", "opaque-handle"),
    ]


def test_unsupported_backend_selector_fails_without_plaintext_fallback():
    with pytest.raises(SecretUnavailableError, match="unsupported"):
        select_secret_provider(
            backend_kind="plaintext",
            config_root=None,
            configured_path=None,
        )


@pytest.mark.skipif(os.name != "nt", reason="legacy backend inference is Windows-only")
def test_existing_windows_identity_without_backend_metadata_remains_compatible(tmp_path):
    config, backend, provider = initialized(tmp_path / "legacy-windows.sqlite")
    config.pop("hask_database_secret_backend")
    writes = backend.writes

    result, repeated = initialize_operational_database_identity(
        config, secret_provider=provider
    )

    assert result.state is DatabaseIdentityInitializationState.ALREADY_INITIALIZED
    assert repeated == config
    assert backend.writes == writes


def test_identity_metadata_saver_replaces_config_without_temporary_residue(
    tmp_path, monkeypatch
):
    from hadocs.utils import config as config_module

    target = tmp_path / "config.json"
    target.write_text('{"existing": true}', encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    config_module.save_database_identity_config(
        {"hask_database_identity_state": "initializing"}
    )

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "hask_database_identity_state": "initializing"
    }
    assert list(tmp_path.glob("*.tmp")) == []


def test_first_initialization_generates_one_uuid_and_one_protected_32_byte_secret(
    tmp_path,
):
    backend = MemoryBackend()
    requested_lengths: list[int] = []

    def secret_factory(length: int) -> bytes:
        requested_lengths.append(length)
        return b"\x91" * length

    provider = CredentialStoreSecretProvider(backend, secret_factory=secret_factory)
    saves: list[dict[str, object]] = []
    result, config = initialize_operational_database_identity(
        base_config(tmp_path / "identity.sqlite"),
        secret_provider=provider,
        uuid_factory=lambda: FIXED_UUID,
        save=lambda value: saves.append(deepcopy(value)),
    )

    assert result.state is DatabaseIdentityInitializationState.INITIALIZED
    assert requested_lengths == [32]
    assert backend.writes == 1
    assert tuple(backend.values.values()) == (b"\x91" * 32,)
    assert config["hask_database_installation_uuid"] == FIXED_UUID
    assert config["hask_database_installation_scope"] == FIXED_SCOPE
    assert config["hask_database_secret_generation"] == 1
    assert config["hask_database_identity_version"] == 1
    assert config["hask_database_identity_state"] == "initialized"
    assert len(saves) == 2
    assert saves[0]["hask_database_identity_state"] == "initializing"
    assert saves[1] == config


def test_only_non_secret_identity_metadata_enters_config(tmp_path):
    secret = bytes(range(32))
    config, _, _ = initialized(tmp_path / "private.sqlite", secret=secret)
    serialized = json.dumps(config, sort_keys=True)
    added = set(config) - set(base_config(tmp_path / "private.sqlite"))

    assert added == {
        "hask_database_enabled",
        "hask_database_identity_version",
        "hask_database_installation_uuid",
        "hask_database_installation_scope",
        "hask_database_secret_handle",
        "hask_database_secret_generation",
        "hask_database_secret_backend",
        "hask_database_identity_state",
    }
    assert secret.hex() not in serialized
    assert base64.b64encode(secret).decode("ascii") not in serialized


def test_repeated_initialization_is_a_validated_no_op(tmp_path):
    config, backend, provider = initialized(tmp_path / "repeat.sqlite")
    before = deepcopy(config)
    writes = backend.writes
    saves: list[dict[str, object]] = []

    result, repeated = initialize_operational_database_identity(
        config,
        secret_provider=provider,
        uuid_factory=lambda: pytest.fail("UUID must not be regenerated"),
        save=lambda value: saves.append(value),
    )

    assert result.state is DatabaseIdentityInitializationState.ALREADY_INITIALIZED
    assert repeated == before
    assert backend.writes == writes
    assert saves == []
    assert provider.load(
        str(config["hask_database_secret_handle"]), 1
    ) == b"\xa7" * 32


@pytest.mark.parametrize(
    ("stored", "message"),
    ((None, "missing"), (b"short", "malformed")),
)
def test_missing_or_malformed_secret_fails_closed(tmp_path, stored, message):
    config, backend, provider = initialized(tmp_path / f"{message}.sqlite")
    handle = str(config["hask_database_secret_handle"])
    if stored is None:
        backend.values.pop(handle)
    else:
        backend.values[handle] = stored

    with pytest.raises(SecretUnavailableError, match=message):
        initialize_operational_database_identity(config, secret_provider=provider)


def test_inaccessible_secret_is_distinguished_without_disclosing_handle(tmp_path):
    config, backend, provider = initialized(tmp_path / "inaccessible.sqlite")
    backend.read_error = PermissionError("denied")

    with pytest.raises(SecretUnavailableError, match="inaccessible") as captured:
        provider.load(str(config["hask_database_secret_handle"]), 1)
    assert FIXED_SCOPE not in str(captured.value)


def test_uuid_scope_mismatch_and_partial_metadata_fail_without_overwrite(tmp_path):
    config, backend, provider = initialized(tmp_path / "mismatch.sqlite")
    original = deepcopy(backend.values)
    config["hask_database_installation_scope"] = "is1_" + "0" * 64
    with pytest.raises(ValueError, match="UUID and scope disagree"):
        initialize_operational_database_identity(config, secret_provider=provider)
    assert backend.values == original

    partial = base_config(tmp_path / "partial.sqlite")
    partial["hask_database_identity_version"] = 1
    with pytest.raises(ValueError, match="partial"):
        initialize_operational_database_identity(partial, secret_provider=provider)
    assert backend.values == original


def test_interrupted_final_save_leaves_detectable_fail_closed_metadata(tmp_path):
    backend = MemoryBackend()
    provider = CredentialStoreSecretProvider(
        backend, secret_factory=lambda length: b"\xb4" * length
    )
    saved: list[dict[str, object]] = []

    def interrupt_final_save(value: dict[str, object]) -> None:
        saved.append(deepcopy(value))
        if value["hask_database_identity_state"] == "initialized":
            raise OSError("synthetic interrupted save")

    with pytest.raises(OSError, match="interrupted"):
        initialize_operational_database_identity(
            base_config(tmp_path / "interrupted.sqlite"),
            secret_provider=provider,
            uuid_factory=lambda: FIXED_UUID,
            save=interrupt_final_save,
        )

    assert saved[0]["hask_database_identity_state"] == "initializing"
    assert len(backend.values) == 1
    writes = backend.writes
    with pytest.raises(ValueError, match="not initialized"):
        initialize_operational_database_identity(
            saved[0], secret_provider=provider
        )
    assert backend.writes == writes


def test_disabled_mode_never_reads_the_secret_store(tmp_path):
    backend = MemoryBackend()
    backend.read_error = AssertionError("disabled mode accessed protected storage")
    provider = CredentialStoreSecretProvider(backend)
    result = persist_operational_database(
        empty_model(),
        {
            "hask_database_enabled": False,
            "hask_database_path": str(tmp_path / "disabled.sqlite"),
        },
        secret_provider=provider,
    )

    assert result.state.value == "disabled"
    assert backend.reads == 0
    assert not (tmp_path / "disabled.sqlite").exists()


def test_enabled_identity_capable_service_rejects_null_provider(tmp_path):
    path = tmp_path / "null.sqlite"
    service = HaskDatabaseService(
        HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path)),
        NullSecretProvider(),
        require_protected_identity=True,
    )
    with pytest.raises(SecretUnavailableError, match="protected secret provider"):
        service.startup()
    assert not path.exists()


def test_enabled_counts_scan_and_restart_use_same_protected_identity(tmp_path):
    path = tmp_path / "counts.sqlite"
    config, backend, provider = initialized(path)
    first = persist_operational_database(
        empty_model(), config, operation=operation(), secret_provider=provider
    )
    reconstructed = CredentialStoreSecretProvider(backend)
    replay = persist_operational_database(
        empty_model(), config, operation=operation(), secret_provider=reconstructed
    )

    assert replay.replay_state == "existing_terminal"
    assert replay.installation_id == first.installation_id
    assert replay.context_id == first.context_id
    assert replay.scan_run_id == first.scan_run_id
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("SELECT count(*) FROM scan_run").fetchone()[0] == 1
        context = connection.execute(
            "SELECT installation_scope,secret_handle,secret_generation "
            "FROM installation_context"
        ).fetchone()
        assert context == (
            FIXED_SCOPE,
            config["hask_database_secret_handle"],
            1,
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256
    finally:
        connection.close()


def test_legacy_no_secret_context_is_rejected_without_rewrite(tmp_path):
    path = tmp_path / "legacy.sqlite"
    factory = HaskSQLiteConnectionFactory(HaskDatabaseConfig(enabled=True, path=path))
    legacy = HaskDatabaseService(factory)
    legacy.startup()
    try:
        legacy.persist_operational_slice(
            OperationalSliceRequest(
                recovery_set_ref="hadocs:installation:synthetic-identity-installation",
                installation_scope="hadocs:normal-scan:v1",
                secret_handle="hadocs:no-secret:v1",
                secret_generation=1,
                context_format_version=1,
                scan_idempotency_key="legacy-running-scan",
                started_at="2026-07-27T13:00:00Z",
                implementation_version="legacy-placeholder",
                contract_version="legacy-placeholder",
                observations=(
                    ObservationInput(
                        observation_key="legacy-counts",
                        taxonomy_class="B",
                        authority_class="STRUCTURED_CONTEXT_DEPENDENT",
                        observed_at="2026-07-27T13:00:00Z",
                        payload={"entities": 0},
                        privacy_class="LOCAL_ONLY",
                        retention_policy="RETAIN_UNTIL_SUPERSEDED",
                    ),
                ),
            )
        )
    finally:
        legacy.shutdown()

    before = sqlite3.connect(path)
    try:
        before_rows = before.execute(
            "SELECT id,installation_scope,secret_handle,secret_generation,status "
            "FROM installation_context"
        ).fetchall()
        before_counts = before.execute("SELECT count(*) FROM scan_run").fetchone()[0]
    finally:
        before.close()

    config, _, provider = initialized(path)
    with pytest.raises(RecoveryModeError, match="legacy placeholder"):
        persist_operational_database(
            empty_model(), config, operation=operation(), secret_provider=provider
        )

    after = sqlite3.connect(path)
    try:
        assert after.execute(
            "SELECT id,installation_scope,secret_handle,secret_generation,status "
            "FROM installation_context"
        ).fetchall() == before_rows
        assert after.execute("SELECT count(*) FROM scan_run").fetchone()[0] == before_counts
    finally:
        after.close()


def test_cli_output_discloses_no_identity_or_secret_material(tmp_path, capsys):
    secret = b"command-output-secret-material!!"[:32]
    backend = MemoryBackend()
    provider = CredentialStoreSecretProvider(
        backend, secret_factory=lambda length: secret
    )
    saved: list[dict[str, object]] = []
    config = base_config(tmp_path / "cli.sqlite") | {
        "token": "SYNTHETIC-HOME-ASSISTANT-TOKEN"
    }

    assert cmd_database_init(
        config_loader=lambda: config,
        config_saver=lambda value: saved.append(value),
        secret_provider=provider,
    ) == 0
    output = capsys.readouterr().out

    assert "initialized successfully" in output
    assert len(saved) == 2
    final_config = saved[-1]
    assert saved[0]["hask_database_identity_state"] == "initializing"
    assert str(final_config["hask_database_installation_uuid"]) not in output
    assert str(final_config["hask_database_installation_scope"]) not in output
    assert str(final_config["hask_database_secret_handle"]) not in output
    assert "SYNTHETIC-HOME-ASSISTANT-TOKEN" not in output
    assert secret.hex() not in output
    assert base64.b64encode(secret).decode("ascii") not in output
    assert "HADocs/DatabaseIdentity/" not in output

    writes = backend.writes
    assert cmd_database_init(
        config_loader=lambda: final_config,
        config_saver=lambda value: pytest.fail("repeat must not save config"),
        secret_provider=provider,
    ) == 0
    repeated_output = capsys.readouterr().out
    assert "already initialized" in repeated_output
    assert backend.writes == writes
    assert str(final_config["hask_database_installation_uuid"]) not in repeated_output
    assert str(final_config["hask_database_secret_handle"]) not in repeated_output


def test_secret_bytes_and_encodings_do_not_enter_database_or_logs(tmp_path, caplog):
    secret = bytes(range(64, 96))
    path = tmp_path / "disclosure.sqlite"
    config, _, provider = initialized(path, secret=secret)
    persist_operational_database(
        empty_model(), config, operation=operation(), secret_provider=provider
    )

    serialized_config = json.dumps(config, sort_keys=True).encode("utf-8")
    database_bytes = path.read_bytes()
    logs = caplog.text.encode("utf-8")
    for prohibited in (
        secret,
        secret.hex().encode("ascii"),
        base64.b64encode(secret),
    ):
        assert prohibited not in serialized_config
        assert prohibited not in database_bytes
        assert prohibited not in logs


def test_enabled_configuration_requires_complete_valid_identity(tmp_path):
    with pytest.raises(ValueError, match="explicitly initialized"):
        HaskDatabaseApplicationConfig.from_application_config(
            base_config(tmp_path / "not-initialized.sqlite")
            | {"hask_database_enabled": True}
        )
