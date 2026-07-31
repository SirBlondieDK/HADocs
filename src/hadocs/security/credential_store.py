"""Secure token storage for HADocs.

On Windows, Home Assistant tokens are stored in Windows Credential Manager
using DPAPI-backed generic credentials. The token should not be stored in
config.json.
"""

from __future__ import annotations

import ctypes
from contextlib import contextmanager
import errno
import hashlib
import os
from pathlib import Path
import stat
from threading import local
from typing import Callable
from uuid import uuid4
from ctypes import wintypes

CREDENTIAL_TARGET = "HADocs/HomeAssistantToken"
CREDENTIAL_USERNAME = "HomeAssistantToken"
DATABASE_IDENTITY_USERNAME = "HADocsDatabaseIdentity"

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2


class CredentialStoreError(RuntimeError):
    pass


POSIX_DATABASE_CREDENTIAL_HEADER = b"HADOCS-DB-IDENTITY\x00\x01"
POSIX_DATABASE_SECRET_LENGTH = 32


class PosixFileCredentialStore:
    """Strict, non-serializing POSIX credential-file store.

    The caller supplies a dedicated credential directory under an established
    persistent root.  Reads never create or repair paths.  Writes atomically
    publish one file without replacing any pre-existing credential.
    """

    _FILE_PREFIX = "database-identity-"
    _FILE_SUFFIX = ".credential"

    def __init__(
        self,
        directory: str | Path,
        *,
        persistent_root: str | Path,
        effective_uid: Callable[[], int] | None = None,
        temporary_name_factory: Callable[[], str] | None = None,
    ) -> None:
        self.directory = Path(directory).absolute()
        self.persistent_root = Path(persistent_root).absolute()
        self._effective_uid = effective_uid or getattr(os, "geteuid", None)
        self._temporary_name_factory = temporary_name_factory or (
            lambda: f".hadocs-credential-{uuid4().hex}.tmp"
        )
        self._lock_state = local()
        try:
            self.directory.relative_to(self.persistent_root)
        except ValueError as error:
            raise CredentialStoreError(
                "credential directory must be inside the persistent root"
            ) from error
        if self.directory == self.persistent_root:
            raise CredentialStoreError(
                "credential directory must be below the persistent root"
            )

    @classmethod
    def alias_for(cls, handle: str) -> str:
        if not isinstance(handle, str) or not handle.strip():
            raise ValueError("protected credential handle must be non-empty text")
        digest = hashlib.sha256(handle.encode("utf-8", errors="strict")).hexdigest()
        return f"{cls._FILE_PREFIX}{digest}{cls._FILE_SUFFIX}"

    def _require_posix(self) -> None:
        if os.name != "posix" or self._effective_uid is None:
            raise CredentialStoreError(
                "secure POSIX credential storage is unavailable on this platform"
            )

    def _uid(self) -> int:
        self._require_posix()
        assert self._effective_uid is not None
        return int(self._effective_uid())

    def _lstat(self, path: Path, *, missing_ok: bool = False):
        try:
            return path.lstat()
        except FileNotFoundError:
            if missing_ok:
                return None
            raise CredentialStoreError("protected credential path is missing") from None
        except OSError as error:
            raise CredentialStoreError(
                "protected credential path could not be validated"
            ) from error

    def _validate_root(self) -> None:
        details = self._lstat(self.persistent_root)
        assert details is not None
        if stat.S_ISLNK(details.st_mode):
            raise CredentialStoreError("persistent credential root must not be a symlink")
        if not stat.S_ISDIR(details.st_mode):
            raise CredentialStoreError("persistent credential root is not a directory")
        if details.st_uid != self._uid():
            raise CredentialStoreError("persistent credential root has the wrong owner")

    def _validate_private_directory(self, path: Path) -> None:
        details = self._lstat(path)
        assert details is not None
        if stat.S_ISLNK(details.st_mode):
            raise CredentialStoreError("credential directory must not be a symlink")
        if not stat.S_ISDIR(details.st_mode):
            raise CredentialStoreError("credential path is not a directory")
        if details.st_uid != self._uid():
            raise CredentialStoreError("credential directory has the wrong owner")
        if stat.S_IMODE(details.st_mode) != 0o700:
            raise CredentialStoreError("credential directory permissions are insecure")

    def _directory_chain(self) -> tuple[Path, ...]:
        relative = self.directory.relative_to(self.persistent_root)
        current = self.persistent_root
        paths: list[Path] = []
        for component in relative.parts:
            current = current / component
            paths.append(current)
        return tuple(paths)

    def _validate_directory(self, *, create: bool) -> None:
        self._validate_root()
        for path in self._directory_chain():
            details = self._lstat(path, missing_ok=True)
            if details is None:
                if not create:
                    raise CredentialStoreError("credential directory is missing")
                try:
                    os.mkdir(path, 0o700)
                except FileExistsError:
                    pass
                except OSError as error:
                    raise CredentialStoreError(
                        "credential directory could not be created securely"
                    ) from error
            self._validate_private_directory(path)

    def _target(self, handle: str) -> Path:
        return self.directory / self.alias_for(handle)

    def _validate_file(self, path: Path):
        details = self._lstat(path)
        assert details is not None
        if stat.S_ISLNK(details.st_mode):
            raise CredentialStoreError("protected credential file must not be a symlink")
        if not stat.S_ISREG(details.st_mode):
            raise CredentialStoreError("protected credential path is not a regular file")
        if details.st_uid != self._uid():
            raise CredentialStoreError("protected credential file has the wrong owner")
        if stat.S_IMODE(details.st_mode) != 0o600:
            raise CredentialStoreError("protected credential file permissions are insecure")
        return details

    @staticmethod
    def _open_no_follow(path: Path, flags: int, mode: int | None = None) -> int:
        no_follow = getattr(os, "O_NOFOLLOW", None)
        if no_follow is None:
            raise CredentialStoreError("no-follow file opens are unavailable")
        flags |= no_follow
        try:
            if mode is None:
                return os.open(path, flags)
            return os.open(path, flags, mode)
        except OSError as error:
            raise CredentialStoreError(
                "protected credential file could not be opened securely"
            ) from error

    def _read_payload(self, path: Path) -> bytes:
        before = self._validate_file(path)
        descriptor = self._open_no_follow(path, os.O_RDONLY)
        try:
            after = os.fstat(descriptor)
            if not stat.S_ISREG(after.st_mode):
                raise CredentialStoreError(
                    "protected credential path is not a regular file"
                )
            if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
                raise CredentialStoreError("protected credential file changed during open")
            if after.st_uid != self._uid() or stat.S_IMODE(after.st_mode) != 0o600:
                raise CredentialStoreError(
                    "protected credential file security changed during open"
                )
            expected = len(POSIX_DATABASE_CREDENTIAL_HEADER) + POSIX_DATABASE_SECRET_LENGTH
            payload = bytearray()
            while len(payload) <= expected:
                chunk = os.read(descriptor, expected + 1 - len(payload))
                if not chunk:
                    break
                payload.extend(chunk)
        finally:
            os.close(descriptor)
        if len(payload) != expected:
            raise CredentialStoreError("protected credential content is malformed")
        header_length = len(POSIX_DATABASE_CREDENTIAL_HEADER)
        if bytes(payload[:header_length]) != POSIX_DATABASE_CREDENTIAL_HEADER:
            raise CredentialStoreError("protected credential format is unsupported")
        return bytes(payload[header_length:])

    @staticmethod
    def _write_all(descriptor: int, payload: bytes) -> None:
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("short protected credential write")
            written += count

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(directory, flags)
        try:
            try:
                os.fsync(descriptor)
            except OSError as error:
                if error.errno not in {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP}:
                    raise
        finally:
            os.close(descriptor)

    @contextmanager
    def _exclusive_directory(self):
        """Serialize creation in the dedicated store without a lock file."""

        import fcntl

        if getattr(self._lock_state, "depth", 0):
            self._lock_state.depth += 1
            try:
                yield
            finally:
                self._lock_state.depth -= 1
            return

        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        no_follow = getattr(os, "O_NOFOLLOW", None)
        if no_follow is None:
            raise CredentialStoreError("no-follow directory opens are unavailable")
        descriptor = os.open(self.directory, flags | no_follow)
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISDIR(opened.st_mode)
                or opened.st_uid != self._uid()
                or stat.S_IMODE(opened.st_mode) != 0o700
            ):
                raise CredentialStoreError(
                    "credential directory security changed during open"
                )
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self._lock_state.depth = 1
            self._validate_private_directory(self.directory)
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                self._lock_state.depth = 0
                os.close(descriptor)

    def _existing_credentials(self) -> tuple[Path, ...]:
        try:
            names = tuple(os.listdir(self.directory))
        except OSError as error:
            raise CredentialStoreError(
                "credential directory could not be inspected securely"
            ) from error
        return tuple(
            self.directory / name
            for name in names
            if name.startswith(self._FILE_PREFIX) and name.endswith(self._FILE_SUFFIX)
        )

    @contextmanager
    def initialization_guard(self):
        """Hold the store lock across pending metadata, secret, and final metadata."""

        self.prepare_for_create()
        with self._exclusive_directory():
            existing = self._existing_credentials()
            for path in existing:
                self._validate_file(path)
            if existing:
                raise CredentialStoreError(
                    "a protected database identity already exists"
                )
            yield

    def write(self, handle: str, value: bytes) -> None:
        self._require_posix()
        if not isinstance(value, bytes) or len(value) != POSIX_DATABASE_SECRET_LENGTH:
            raise CredentialStoreError("protected credential must contain exactly 32 bytes")
        self._validate_directory(create=True)
        with self._exclusive_directory():
            self._write_exclusive(handle, value)

    def prepare_for_create(self) -> None:
        """Create only missing private directories during explicit init."""

        self._require_posix()
        self._validate_directory(create=True)

    def _write_exclusive(self, handle: str, value: bytes) -> None:
        target = self._target(handle)
        if self._lstat(target, missing_ok=True) is not None:
            self._validate_file(target)
            raise CredentialStoreError("protected credential already exists")

        for existing in self._existing_credentials():
            self._validate_file(existing)
            if existing != target:
                raise CredentialStoreError(
                    "a conflicting protected credential already exists"
                )

        temporary_name = self._temporary_name_factory()
        if (
            not temporary_name
            or Path(temporary_name).name != temporary_name
            or not temporary_name.startswith(".hadocs-credential-")
            or not temporary_name.endswith(".tmp")
        ):
            raise CredentialStoreError("temporary credential name is invalid")
        temporary = self.directory / temporary_name
        if self._lstat(temporary, missing_ok=True) is not None:
            raise CredentialStoreError("temporary credential path already exists")

        descriptor: int | None = None
        temporary_removed = False
        payload = POSIX_DATABASE_CREDENTIAL_HEADER + value
        try:
            descriptor = self._open_no_follow(
                temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
            self._validate_file(temporary)
            self._write_all(descriptor, payload)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            self._validate_file(temporary)
            try:
                os.link(temporary, target, follow_symlinks=False)
            except FileExistsError as error:
                raise CredentialStoreError("protected credential already exists") from error
            temporary.unlink()
            temporary_removed = True
            self._fsync_directory(self.directory)
        except CredentialStoreError:
            raise
        except OSError as error:
            raise CredentialStoreError(
                "protected credential could not be stored securely"
            ) from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if not temporary_removed:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as error:
                    raise CredentialStoreError(
                        "temporary credential could not be removed securely"
                    ) from error
        stored = self._read_payload(target)
        if stored != value:
            raise CredentialStoreError("protected credential storage validation failed")

    def read(self, handle: str) -> bytes | None:
        self._require_posix()
        self._validate_directory(create=False)
        target = self._target(handle)
        if self._lstat(target, missing_ok=True) is None:
            return None
        return self._read_payload(target)

    def delete(self, handle: str) -> bool:
        self._require_posix()
        self._validate_directory(create=False)
        target = self._target(handle)
        if self._lstat(target, missing_ok=True) is None:
            return False
        self._validate_file(target)
        try:
            target.unlink()
            self._fsync_directory(self.directory)
        except OSError as error:
            raise CredentialStoreError(
                "protected credential could not be removed securely"
            ) from error
        return True


ERROR_NOT_FOUND = 1168


def is_windows_credential_manager_available() -> bool:
    return os.name == "nt"


if os.name == "nt":
    class FILETIME(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", wintypes.DWORD),
            ("dwHighDateTime", wintypes.DWORD),
        ]


    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]


    PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    CredWriteW = advapi32.CredWriteW
    CredWriteW.argtypes = [PCREDENTIALW, wintypes.DWORD]
    CredWriteW.restype = wintypes.BOOL

    CredReadW = advapi32.CredReadW
    CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIALW)]
    CredReadW.restype = wintypes.BOOL

    CredDeleteW = advapi32.CredDeleteW
    CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    CredDeleteW.restype = wintypes.BOOL

    CredFree = advapi32.CredFree
    CredFree.argtypes = [ctypes.c_void_p]
    CredFree.restype = None


def _raise_last_error(action: str) -> None:
    error = ctypes.get_last_error()
    raise CredentialStoreError(f"Windows Credential Manager failed during {action}. WinError={error}")


def set_protected_binary_credential(
    target: str,
    value: bytes,
    *,
    username: str = DATABASE_IDENTITY_USERNAME,
    comment: str = "HADocs protected database identity",
) -> None:
    """Store an opaque binary value in the platform credential manager."""

    if not isinstance(target, str) or not target.strip():
        raise ValueError("protected credential target must be non-empty text")
    if not isinstance(value, bytes) or not value:
        raise ValueError("protected credential value must be non-empty bytes")
    if not is_windows_credential_manager_available():
        raise CredentialStoreError("protected credential storage is unavailable")

    blob = ctypes.create_string_buffer(value, len(value))
    credential = CREDENTIALW()
    credential.Flags = 0
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = target
    credential.Comment = comment
    credential.CredentialBlobSize = len(value)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(wintypes.BYTE))
    credential.Persist = CRED_PERSIST_LOCAL_MACHINE
    credential.AttributeCount = 0
    credential.Attributes = None
    credential.TargetAlias = None
    credential.UserName = username

    if not CredWriteW(ctypes.byref(credential), 0):
        _raise_last_error("protected credential write")


def get_protected_binary_credential(target: str) -> bytes | None:
    """Read an opaque binary value without decoding or logging it."""

    if not isinstance(target, str) or not target.strip():
        raise ValueError("protected credential target must be non-empty text")
    if not is_windows_credential_manager_available():
        raise CredentialStoreError("protected credential storage is unavailable")

    credential_ptr = PCREDENTIALW()
    if not CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(credential_ptr)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return None
        raise CredentialStoreError(
            "Windows Credential Manager failed during protected credential read. "
            f"WinError={error}"
        )

    try:
        credential = credential_ptr.contents
        if not credential.CredentialBlob or credential.CredentialBlobSize == 0:
            return b""
        return ctypes.string_at(
            credential.CredentialBlob, credential.CredentialBlobSize
        )
    finally:
        CredFree(credential_ptr)


def delete_protected_binary_credential(target: str) -> bool:
    """Delete one explicitly named protected credential."""

    if not isinstance(target, str) or not target.strip():
        raise ValueError("protected credential target must be non-empty text")
    if not is_windows_credential_manager_available():
        raise CredentialStoreError("protected credential storage is unavailable")
    if CredDeleteW(target, CRED_TYPE_GENERIC, 0):
        return True
    error = ctypes.get_last_error()
    if error == ERROR_NOT_FOUND:
        return False
    raise CredentialStoreError(
        "Windows Credential Manager failed during protected credential delete. "
        f"WinError={error}"
    )


def set_home_assistant_token(token: str) -> bool:
    if not token:
        return False

    if not is_windows_credential_manager_available():
        return False

    encoded = token.encode("utf-16-le")
    blob = ctypes.create_string_buffer(encoded)

    credential = CREDENTIALW()
    credential.Flags = 0
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = CREDENTIAL_TARGET
    credential.Comment = "HADocs Home Assistant Long-Lived Access Token"
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(wintypes.BYTE))
    credential.Persist = CRED_PERSIST_LOCAL_MACHINE
    credential.AttributeCount = 0
    credential.Attributes = None
    credential.TargetAlias = None
    credential.UserName = CREDENTIAL_USERNAME

    if not CredWriteW(ctypes.byref(credential), 0):
        _raise_last_error("write")

    return True


def get_home_assistant_token() -> str | None:
    if not is_windows_credential_manager_available():
        return None

    credential_ptr = PCREDENTIALW()
    if not CredReadW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(credential_ptr)):
        return None

    try:
        credential = credential_ptr.contents
        if not credential.CredentialBlob or credential.CredentialBlobSize == 0:
            return None

        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        return raw.decode("utf-16-le")
    finally:
        CredFree(credential_ptr)


def delete_home_assistant_token() -> bool:
    if not is_windows_credential_manager_available():
        return False
    return bool(CredDeleteW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0))


def has_home_assistant_token() -> bool:
    return bool(get_home_assistant_token())


def migrate_plaintext_token_from_config(config: dict) -> dict:
    clean = dict(config or {})
    token = clean.pop("token", None) or clean.pop("ha_token", None)

    if token:
        set_home_assistant_token(str(token))

    return clean


def inject_token_into_runtime_config(config: dict) -> dict:
    runtime = dict(config or {})
    token = get_home_assistant_token()
    if token:
        runtime["token"] = token
    return runtime
