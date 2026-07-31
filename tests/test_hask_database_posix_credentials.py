from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
from pathlib import Path
import stat
from threading import Barrier
from threading import Lock

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
    CredentialStoreSecretProvider,
    POSIX_FILE_CREDENTIAL_BACKEND,
    PosixFileCredentialBackend,
    SecretUnavailableError,
    resolve_posix_credential_location,
    select_secret_provider,
)
from hadocs.security.credential_store import (
    CredentialStoreError,
    POSIX_DATABASE_CREDENTIAL_HEADER,
    PosixFileCredentialStore,
)


FIXED_UUID = "123e4567-e89b-42d3-a456-426614174000"


pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="strict POSIX filesystem semantics required"
)


def _store(tmp_path: Path, **kwargs) -> tuple[PosixFileCredentialStore, Path, Path]:
    root = tmp_path / "persistent"
    root.mkdir(mode=0o755)
    directory = root / ".hadocs" / "credentials"
    return (
        PosixFileCredentialStore(directory, persistent_root=root, **kwargs),
        root,
        directory,
    )


def _target(store: PosixFileCredentialStore, directory: Path, handle: str) -> Path:
    return directory / store.alias_for(handle)


def _provider(tmp_path: Path, secret: bytes = b"\x8d" * 32):
    store, root, directory = _store(tmp_path)
    backend = PosixFileCredentialBackend(directory, persistent_root=root)
    provider = CredentialStoreSecretProvider(
        backend,
        backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
        secret_factory=lambda length: secret if length == 32 else b"",
    )
    return provider, store, root, directory


def _base_config(tmp_path: Path) -> dict[str, object]:
    return {
        "hask_database_path": str(tmp_path / "operational.sqlite"),
        "hask_database_installation_ref": "synthetic-posix-installation",
    }


def _empty_model() -> InstallationModel:
    return InstallationModel(
        areas={}, devices={}, entities={}, integrations={}, config={},
        states=[], services=[], labels=[], raw={}
    )


def test_posix_initialization_writes_one_stable_secret_with_strict_modes(tmp_path):
    provider, _, root, directory = _provider(tmp_path)
    result, config = initialize_operational_database_identity(
        _base_config(tmp_path),
        secret_provider=provider,
        uuid_factory=lambda: FIXED_UUID,
    )

    files = list(directory.glob("database-identity-*.credential"))
    assert result.state is DatabaseIdentityInitializationState.INITIALIZED
    assert config["hask_database_secret_backend"] == POSIX_FILE_CREDENTIAL_BACKEND
    assert len(files) == 1
    assert stat.S_IMODE((root / ".hadocs").stat().st_mode) == 0o700
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(files[0].stat().st_mode) == 0o600
    assert files[0].stat().st_size == len(POSIX_DATABASE_CREDENTIAL_HEADER) + 32

    reconstructed = CredentialStoreSecretProvider(
        PosixFileCredentialBackend(directory, persistent_root=root),
        backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
    )
    handle = str(config["hask_database_secret_handle"])
    assert reconstructed.load(handle, 1) == b"\x8d" * 32
    before = files[0].stat()
    repeated, unchanged = initialize_operational_database_identity(
        config, secret_provider=reconstructed
    )
    assert repeated.state is DatabaseIdentityInitializationState.ALREADY_INITIALIZED
    assert unchanged == config
    assert files[0].stat().st_ino == before.st_ino
    assert files[0].stat().st_mtime_ns == before.st_mtime_ns


def test_missing_persistent_root_fails_closed(tmp_path):
    missing = tmp_path / "missing"
    store = PosixFileCredentialStore(
        missing / ".hadocs" / "credentials", persistent_root=missing
    )
    with pytest.raises(CredentialStoreError, match="missing"):
        store.write("handle", b"x" * 32)


def test_posix_selection_requires_explicit_store_or_exact_config_root(tmp_path):
    with pytest.raises(SecretUnavailableError, match="persistent.*path"):
        select_secret_provider(
            backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
            config_root=tmp_path,
            configured_path=None,
        )
    with pytest.raises(SecretUnavailableError, match="temporary"):
        select_secret_provider(
            backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
            config_root=None,
            configured_path=tmp_path / "credentials",
        )


def test_exact_config_root_uses_preferred_persistent_layout(monkeypatch):
    original_exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda path: True if path == Path("/config") else original_exists(path),
    )
    directory, root = resolve_posix_credential_location(
        config_root=Path("/config"), configured_path=None
    )

    assert root == Path("/config")
    assert directory == Path("/config/.hadocs/credentials")


def test_symlink_directory_target_and_temporary_are_rejected(tmp_path):
    store, root, directory = _store(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (root / ".hadocs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(CredentialStoreError, match="symlink"):
        store.write("directory-link", b"a" * 32)

    (root / ".hadocs").unlink()
    store.write("seed", b"s" * 32)
    target = _target(store, directory, "target-link")
    target.symlink_to(_target(store, directory, "seed"))
    with pytest.raises(CredentialStoreError, match="symlink"):
        store.read("target-link")

    second_root = tmp_path / "second-persistent"
    second_root.mkdir(mode=0o755)
    second_directory = second_root / ".hadocs" / "credentials"
    fixed_temp = ".hadocs-credential-fixed.tmp"
    isolated = PosixFileCredentialStore(
        second_directory,
        persistent_root=second_root,
        temporary_name_factory=lambda: fixed_temp,
    )
    isolated.prepare_for_create()
    temp_path = second_directory / fixed_temp
    temp_path.symlink_to(_target(store, directory, "seed"))
    with pytest.raises(CredentialStoreError, match="temporary"):
        isolated.write("second", b"b" * 32)


def test_non_regular_insecure_and_wrong_owner_targets_fail_closed(tmp_path, monkeypatch):
    store, _, directory = _store(tmp_path)
    store._validate_directory(create=True)

    directory_target = _target(store, directory, "directory")
    directory_target.mkdir(mode=0o700)
    with pytest.raises(CredentialStoreError, match="regular"):
        store.read("directory")

    insecure = _target(store, directory, "insecure")
    insecure.write_bytes(POSIX_DATABASE_CREDENTIAL_HEADER + b"i" * 32)
    insecure.chmod(0o644)
    with pytest.raises(CredentialStoreError, match="permissions"):
        store.read("insecure")

    owned = _target(store, directory, "owner")
    owned.write_bytes(POSIX_DATABASE_CREDENTIAL_HEADER + b"o" * 32)
    owned.chmod(0o600)
    actual_uid = os.geteuid()
    original_validate_root = store._validate_root
    original_validate_directory = store._validate_private_directory
    monkeypatch.setattr(store, "_validate_root", lambda: None)
    monkeypatch.setattr(store, "_validate_private_directory", lambda path: None)
    monkeypatch.setattr(store, "_effective_uid", lambda: actual_uid + 1)
    with pytest.raises(CredentialStoreError, match="wrong owner"):
        store.read("owner")
    monkeypatch.setattr(store, "_validate_root", original_validate_root)
    monkeypatch.setattr(store, "_validate_private_directory", original_validate_directory)


@pytest.mark.parametrize(
    "payload",
    [
        POSIX_DATABASE_CREDENTIAL_HEADER + b"x" * 31,
        POSIX_DATABASE_CREDENTIAL_HEADER + b"x" * 33,
        b"WRONG" + b"x" * 32,
    ],
)
def test_malformed_truncated_oversized_or_wrong_format_content_is_rejected(
    tmp_path, payload
):
    store, _, directory = _store(tmp_path)
    store._validate_directory(create=True)
    target = _target(store, directory, "malformed")
    target.write_bytes(payload)
    target.chmod(0o600)
    with pytest.raises(CredentialStoreError, match="malformed|format"):
        store.read("malformed")


def test_partial_write_leaves_no_target_or_temporary_residue(tmp_path, monkeypatch):
    store, _, directory = _store(tmp_path)

    def partial(descriptor: int, payload: bytes) -> None:
        os.write(descriptor, payload[:7])
        raise OSError("synthetic partial write")

    monkeypatch.setattr(store, "_write_all", partial)
    with pytest.raises(CredentialStoreError, match="stored securely"):
        store.write("partial", b"p" * 32)
    assert not _target(store, directory, "partial").exists()
    assert list(directory.glob("*.tmp")) == []


def test_concurrent_initialization_has_one_winner_without_corruption(tmp_path):
    store, root, directory = _store(tmp_path)
    barrier = Barrier(2)

    def attempt(number: int):
        local = PosixFileCredentialStore(directory, persistent_root=root)
        barrier.wait()
        try:
            local.write(f"concurrent-{number}", bytes([number]) * 32)
            return "created"
        except CredentialStoreError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(attempt, (1, 2)))
    files = list(directory.glob("database-identity-*.credential"))
    assert outcomes.count("created") == 1
    assert len(files) == 1
    assert stat.S_IMODE(files[0].stat().st_mode) == 0o600
    assert files[0].read_bytes().startswith(POSIX_DATABASE_CREDENTIAL_HEADER)


def test_concurrent_full_initialization_leaves_one_final_identity(tmp_path):
    _, root, directory = _store(tmp_path)
    barrier = Barrier(2)
    save_lock = Lock()
    saves: list[dict[str, object]] = []
    uuids = (
        "123e4567-e89b-42d3-a456-426614174000",
        "123e4567-e89b-42d3-a456-426614174001",
    )

    def save(value: dict[str, object]) -> None:
        with save_lock:
            saves.append(deepcopy(value))

    def attempt(number: int):
        provider = CredentialStoreSecretProvider(
            PosixFileCredentialBackend(directory, persistent_root=root),
            backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
            secret_factory=lambda length: bytes([number + 1]) * length,
        )
        barrier.wait()
        try:
            result, config = initialize_operational_database_identity(
                _base_config(tmp_path),
                secret_provider=provider,
                uuid_factory=lambda: uuids[number],
                save=save,
            )
            return result.state.value, config
        except SecretUnavailableError as error:
            return "conflict", str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(attempt, (0, 1)))

    assert sorted(outcome[0] for outcome in outcomes) == ["conflict", "initialized"]
    assert [save["hask_database_identity_state"] for save in saves] == [
        "initializing",
        "initialized",
    ]
    assert len(list(directory.glob("database-identity-*.credential"))) == 1


def test_posix_counts_persistence_and_restart_replay_reuse_identity(tmp_path):
    provider, _, root, directory = _provider(tmp_path)
    _, config = initialize_operational_database_identity(
        _base_config(tmp_path),
        secret_provider=provider,
        uuid_factory=lambda: FIXED_UUID,
    )
    config["hask_database_enabled"] = True
    operation = OperationalDatabaseOperation(
        identity="posix-restart",
        started_at="2026-07-27T18:00:00Z",
        terminal_at="2026-07-27T18:00:01Z",
    )
    first = persist_operational_database(
        _empty_model(), config, operation=operation, secret_provider=provider
    )
    reconstructed = CredentialStoreSecretProvider(
        PosixFileCredentialBackend(directory, persistent_root=root),
        backend_kind=POSIX_FILE_CREDENTIAL_BACKEND,
    )
    replay = persist_operational_database(
        _empty_model(), config, operation=operation, secret_provider=reconstructed
    )
    assert replay.replay_state == "existing_terminal"
    assert replay.scan_run_id == first.scan_run_id
    assert replay.installation_id == first.installation_id


def test_posix_cli_output_and_failures_disclose_no_secret_representation(
    tmp_path, capsys
):
    secret = bytes(range(32))
    provider, _, _, directory = _provider(tmp_path, secret)
    saves: list[dict[str, object]] = []
    assert cmd_database_init(
        config_loader=lambda: _base_config(tmp_path),
        config_saver=lambda value: saves.append(dict(value)),
        secret_provider=provider,
    ) == 0
    output = capsys.readouterr().out
    assert secret.hex() not in output
    assert base64.b64encode(secret).decode("ascii") not in output
    assert "HADocs/DatabaseIdentity/" not in output

    credential = next(directory.glob("database-identity-*.credential"))
    credential.chmod(0o644)
    assert cmd_database_init(
        config_loader=lambda: saves[-1],
        config_saver=lambda value: pytest.fail("must not rewrite"),
        secret_provider=provider,
    ) == 2
    failure = capsys.readouterr().out
    assert secret.hex() not in failure
    assert base64.b64encode(secret).decode("ascii") not in failure
    assert "HADocs/DatabaseIdentity/" not in failure
