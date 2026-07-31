from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hmac
import os
from pathlib import Path
import re
import secrets
from contextlib import contextmanager
from typing import Callable, Protocol, runtime_checkable

from .errors import SecretUnavailableError


_SCOPE_PATTERN = re.compile(r"is1_[0-9a-f]{64}")
_HANDLE_PATTERN = re.compile(
    r"HADocs/DatabaseIdentity/(is1_[0-9a-f]{64})/([1-9][0-9]*)"
)
WINDOWS_CREDENTIAL_BACKEND = "windows_credential_manager"
POSIX_FILE_CREDENTIAL_BACKEND = "posix_file"
SUPPORTED_CREDENTIAL_BACKENDS = frozenset(
    {WINDOWS_CREDENTIAL_BACKEND, POSIX_FILE_CREDENTIAL_BACKEND}
)


class SecretState(str, Enum):
    ABSENT = "absent"
    CREATED = "created"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class SecretDescriptor:
    """Non-secret provider metadata safe to pass through dependency injection."""

    state: SecretState
    provider: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SecretReference:
    """Opaque, non-secret handle and generation returned by a provider."""

    handle: str
    generation: int


@runtime_checkable
class SecretProvider(Protocol):
    """Platform-neutral protected-secret boundary from DB-001G."""

    def describe(self) -> SecretDescriptor: ...

    def create(self, recovery_set_id: str) -> SecretReference: ...

    def load(self, handle: str, generation: int) -> bytes: ...

    def validate(self, handle: str, generation: int) -> SecretDescriptor: ...

    def export_for_recovery(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> bytes: ...

    def restore(self, protected_item: bytes, recovery_set_id: str) -> SecretReference: ...

    def rotate(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> SecretReference: ...

    def destroy(self, handle: str, generation: int) -> None: ...


@runtime_checkable
class ProtectedSecretBackend(Protocol):
    """Minimal protected binary store used by the concrete provider."""

    def write(self, handle: str, value: bytes) -> None: ...

    def read(self, handle: str) -> bytes | None: ...

    def delete(self, handle: str) -> bool: ...


class CredentialStoreBackend:
    """HADocs credential-store adapter without secret serialization."""

    backend_kind = WINDOWS_CREDENTIAL_BACKEND

    def write(self, handle: str, value: bytes) -> None:
        from hadocs.security.credential_store import set_protected_binary_credential

        set_protected_binary_credential(handle, value)

    def read(self, handle: str) -> bytes | None:
        from hadocs.security.credential_store import get_protected_binary_credential

        return get_protected_binary_credential(handle)

    def delete(self, handle: str) -> bool:
        from hadocs.security.credential_store import delete_protected_binary_credential

        return delete_protected_binary_credential(handle)


class PosixFileCredentialBackend:
    """Protected-secret adapter for a persistent POSIX credential directory."""

    backend_kind = POSIX_FILE_CREDENTIAL_BACKEND

    def __init__(self, directory: Path, *, persistent_root: Path) -> None:
        from hadocs.security.credential_store import PosixFileCredentialStore

        self.directory = directory
        self._store = PosixFileCredentialStore(
            directory,
            persistent_root=persistent_root,
        )

    def write(self, handle: str, value: bytes) -> None:
        self._store.write(handle, value)

    def prepare_for_create(self) -> None:
        self._store.prepare_for_create()

    def initialization_guard(self):
        return self._store.initialization_guard()

    def read(self, handle: str) -> bytes | None:
        return self._store.read(handle)

    def delete(self, handle: str) -> bool:
        return self._store.delete(handle)


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_posix_credential_location(
    *,
    config_root: Path | None,
    configured_path: str | Path | None,
) -> tuple[Path, Path]:
    """Resolve only an explicit store or the established ``/config`` root."""

    if os.name != "posix":
        raise SecretUnavailableError("POSIX protected credential storage is unavailable")

    if configured_path is not None and str(configured_path).strip():
        raw_directory = Path(str(configured_path).strip()).expanduser()
        if not raw_directory.is_absolute():
            raise SecretUnavailableError(
                "POSIX credential-store path must be absolute"
            )
        if ".." in raw_directory.parts:
            raise SecretUnavailableError(
                "POSIX credential-store path must not contain parent traversal"
            )
        directory = raw_directory.absolute()
        if directory.parent.name == ".hadocs":
            persistent_root = directory.parent.parent
        else:
            persistent_root = directory.parent
    else:
        if config_root is None or Path(config_root).absolute() != Path("/config"):
            raise SecretUnavailableError(
                "a persistent POSIX credential-store path is required"
            )
        persistent_root = Path("/config")
        directory = persistent_root / ".hadocs" / "credentials"

    temporary_root = Path("/tmp")
    if directory == temporary_root or _path_is_within(directory, temporary_root):
        raise SecretUnavailableError("temporary credential storage is not permitted")

    working_root = Path.cwd().absolute()
    if working_root != Path("/") and _path_is_within(directory, working_root):
        raise SecretUnavailableError("working-directory credential storage is not permitted")

    package_root = Path(__file__).absolute().parent
    if _path_is_within(directory, package_root):
        raise SecretUnavailableError("packaged-source credential storage is not permitted")
    if not persistent_root.exists():
        raise SecretUnavailableError("persistent credential root is missing")
    return directory, persistent_root


def select_secret_provider(
    *,
    backend_kind: str | None,
    config_root: Path | None,
    configured_path: str | Path | None,
) -> CredentialStoreSecretProvider:
    """Select one protected backend without plaintext fallback."""

    selected = backend_kind
    if selected is None:
        if os.name == "nt":
            selected = WINDOWS_CREDENTIAL_BACKEND
        elif os.name == "posix":
            selected = POSIX_FILE_CREDENTIAL_BACKEND
        else:
            raise SecretUnavailableError("no protected credential backend is supported")
    if selected not in SUPPORTED_CREDENTIAL_BACKENDS:
        raise SecretUnavailableError("configured protected credential backend is unsupported")
    if selected == WINDOWS_CREDENTIAL_BACKEND:
        if os.name != "nt":
            raise SecretUnavailableError(
                "Windows Credential Manager backend is unavailable"
            )
        return CredentialStoreSecretProvider(
            CredentialStoreBackend(), backend_kind=selected
        )
    directory, persistent_root = resolve_posix_credential_location(
        config_root=config_root,
        configured_path=configured_path,
    )
    return CredentialStoreSecretProvider(
        PosixFileCredentialBackend(directory, persistent_root=persistent_root),
        backend_kind=selected,
    )


class CredentialStoreSecretProvider:
    """CA-001 secret provider backed by protected HADocs credentials."""

    PROVIDER_NAME = "hadocs_credential_store"

    def __init__(
        self,
        backend: ProtectedSecretBackend | None = None,
        *,
        secret_factory: Callable[[int], bytes] = secrets.token_bytes,
        backend_kind: str | None = None,
    ) -> None:
        self._backend = backend or CredentialStoreBackend()
        self._secret_factory = secret_factory
        inferred_kind = getattr(self._backend, "backend_kind", None)
        self.backend_kind = backend_kind or inferred_kind or WINDOWS_CREDENTIAL_BACKEND
        if self.backend_kind not in SUPPORTED_CREDENTIAL_BACKENDS:
            raise ValueError("protected credential backend kind is unsupported")

    @staticmethod
    def handle_for(installation_scope: str, generation: int) -> str:
        if not isinstance(installation_scope, str) or not _SCOPE_PATTERN.fullmatch(
            installation_scope
        ):
            raise SecretUnavailableError("installation scope is invalid")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
            raise SecretUnavailableError("secret generation is invalid")
        return f"HADocs/DatabaseIdentity/{installation_scope}/{generation}"

    @staticmethod
    def _validate_handle(handle: str, generation: int) -> None:
        if not isinstance(handle, str):
            raise SecretUnavailableError("protected secret handle is invalid")
        match = _HANDLE_PATTERN.fullmatch(handle)
        if match is None or int(match.group(2)) != generation:
            raise SecretUnavailableError("protected secret handle or generation is invalid")

    def _read(self, handle: str) -> bytes | None:
        try:
            return self._backend.read(handle)
        except SecretUnavailableError:
            raise
        except Exception as error:
            raise SecretUnavailableError(
                "protected identity secret is inaccessible"
            ) from error

    def describe(self) -> SecretDescriptor:
        return SecretDescriptor(SecretState.AVAILABLE, self.PROVIDER_NAME)

    @contextmanager
    def initialization_guard(self):
        guard = getattr(self._backend, "initialization_guard", None)
        if guard is None:
            yield
            return
        try:
            with guard():
                yield
        except SecretUnavailableError:
            raise
        except Exception as error:
            raise SecretUnavailableError(
                "protected identity initialization is already in progress or complete"
            ) from error

    def create(self, recovery_set_id: str) -> SecretReference:
        handle = self.handle_for(recovery_set_id, 1)
        prepare = getattr(self._backend, "prepare_for_create", None)
        if prepare is not None:
            try:
                prepare()
            except Exception as error:
                raise SecretUnavailableError(
                    "protected identity secret storage could not be initialized"
                ) from error
        if self._read(handle) is not None:
            raise SecretUnavailableError("protected identity secret already exists")

        secret = self._secret_factory(32)
        if not isinstance(secret, bytes) or len(secret) != 32:
            raise SecretUnavailableError(
                "secure generator did not return exactly 32 secret bytes"
            )
        try:
            self._backend.write(handle, secret)
        except Exception as error:
            raise SecretUnavailableError(
                "protected identity secret could not be stored"
            ) from error

        stored = self._read(handle)
        if stored is None or len(stored) != 32 or not hmac.compare_digest(stored, secret):
            try:
                self._backend.delete(handle)
            except Exception:
                pass
            raise SecretUnavailableError(
                "protected identity secret failed storage validation"
            )
        return SecretReference(handle=handle, generation=1)

    def load(self, handle: str, generation: int) -> bytes:
        self._validate_handle(handle, generation)
        value = self._read(handle)
        if value is None:
            raise SecretUnavailableError("protected identity secret is missing")
        if len(value) != 32:
            raise SecretUnavailableError("protected identity secret is malformed")
        return value

    def validate(self, handle: str, generation: int) -> SecretDescriptor:
        try:
            self.load(handle, generation)
        except SecretUnavailableError as error:
            return SecretDescriptor(
                SecretState.UNAVAILABLE,
                self.PROVIDER_NAME,
                str(error),
            )
        return SecretDescriptor(SecretState.AVAILABLE, self.PROVIDER_NAME)

    def export_for_recovery(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> bytes:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("secret export is not supported")

    def restore(self, protected_item: bytes, recovery_set_id: str) -> SecretReference:
        del protected_item, recovery_set_id
        raise SecretUnavailableError("secret restore is not supported")

    def rotate(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> SecretReference:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("secret rotation is not supported")

    def destroy(self, handle: str, generation: int) -> None:
        self._validate_handle(handle, generation)
        try:
            self._backend.delete(handle)
        except Exception as error:
            raise SecretUnavailableError(
                "protected identity secret could not be removed"
            ) from error


class NullSecretProvider:
    """Safe default: no secret is created, regenerated, or returned."""

    def describe(self) -> SecretDescriptor:
        return SecretDescriptor(SecretState.ABSENT, "null", "provider_not_configured")

    def create(self, recovery_set_id: str) -> SecretReference:
        del recovery_set_id
        raise SecretUnavailableError("no protected secret provider is configured")

    def load(self, handle: str, generation: int) -> bytes:
        del handle, generation
        raise SecretUnavailableError("no protected secret provider is configured")

    def validate(self, handle: str, generation: int) -> SecretDescriptor:
        del handle, generation
        return self.describe()

    def export_for_recovery(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> bytes:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("no protected secret provider is configured")

    def restore(self, protected_item: bytes, recovery_set_id: str) -> SecretReference:
        del protected_item, recovery_set_id
        raise SecretUnavailableError("no protected secret provider is configured")

    def rotate(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> SecretReference:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("no protected secret provider is configured")

    def destroy(self, handle: str, generation: int) -> None:
        del handle, generation
        raise SecretUnavailableError("no protected secret provider is configured")


class LinuxContainerSecretProviderPlaceholder:
    """Non-functional adapter marker pending a separately approved threat review."""

    def describe(self) -> SecretDescriptor:
        return SecretDescriptor(
            SecretState.UNAVAILABLE,
            "linux_container_placeholder",
            "backend_not_implemented",
        )

    def create(self, recovery_set_id: str) -> SecretReference:
        del recovery_set_id
        raise SecretUnavailableError("Linux/container secret backend is not implemented")

    def load(self, handle: str, generation: int) -> bytes:
        del handle, generation
        raise SecretUnavailableError("Linux/container secret backend is not implemented")

    def validate(self, handle: str, generation: int) -> SecretDescriptor:
        del handle, generation
        return self.describe()

    def export_for_recovery(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> bytes:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("Linux/container secret backend is not implemented")

    def restore(self, protected_item: bytes, recovery_set_id: str) -> SecretReference:
        del protected_item, recovery_set_id
        raise SecretUnavailableError("Linux/container secret backend is not implemented")

    def rotate(
        self, handle: str, generation: int, recovery_set_id: str
    ) -> SecretReference:
        del handle, generation, recovery_set_id
        raise SecretUnavailableError("Linux/container secret backend is not implemented")

    def destroy(self, handle: str, generation: int) -> None:
        del handle, generation
        raise SecretUnavailableError("Linux/container secret backend is not implemented")
