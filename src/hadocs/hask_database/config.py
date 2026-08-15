from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import struct
import unicodedata
from uuid import RFC_4122, UUID


IDENTITY_VERSION = 1
IDENTITY_STATE = "initialized"
WINDOWS_CREDENTIAL_BACKEND = "windows_credential_manager"
POSIX_FILE_CREDENTIAL_BACKEND = "posix_file"
SUPPORTED_CREDENTIAL_BACKENDS = frozenset(
    {WINDOWS_CREDENTIAL_BACKEND, POSIX_FILE_CREDENTIAL_BACKEND}
)
_LEGACY_IDENTITY_CONFIG_KEYS = (
    "hask_database_identity_version",
    "hask_database_installation_uuid",
    "hask_database_installation_scope",
    "hask_database_secret_handle",
    "hask_database_secret_generation",
    "hask_database_identity_state",
)
IDENTITY_CONFIG_KEYS = _LEGACY_IDENTITY_CONFIG_KEYS + (
    "hask_database_secret_backend",
)
_SCOPE_PATTERN = re.compile(r"is1_[0-9a-f]{64}")
_SECRET_HANDLE_PATTERN = re.compile(
    r"HADocs/DatabaseIdentity/is1_[0-9a-f]{64}/[1-9][0-9]*"
)
_SCOPE_DOMAIN = "hadocs-generic-metadata/installation-scope/v1"


def _runtime_data_path(value: str) -> Path:
    from hadocs.platform.paths import AppPaths

    return AppPaths.discover().resolve_data_path(value)


def _frame(value: str) -> bytes:
    normalized = unicodedata.normalize("NFC", value)
    encoded = normalized.encode("utf-8", errors="strict")
    return struct.pack(">I", len(encoded)) + encoded


def canonical_installation_uuid(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("database installation UUID is invalid")
    try:
        parsed = UUID(value)
    except (AttributeError, ValueError) as error:
        raise ValueError("database installation UUID is invalid") from error
    if (
        str(parsed) != value
        or parsed.version != 4
        or parsed.variant != RFC_4122
    ):
        raise ValueError("database installation UUID must be canonical RFC 4122 UUIDv4")
    return value


def derive_installation_scope(installation_uuid: str) -> str:
    canonical = canonical_installation_uuid(installation_uuid)
    digest = hashlib.sha256(
        _frame(_SCOPE_DOMAIN) + _frame(canonical)
    ).hexdigest()
    return f"is1_{digest}"


@dataclass(frozen=True, slots=True)
class HaskDatabaseIdentityConfig:
    version: int
    installation_uuid: str
    installation_scope: str
    secret_handle: str
    secret_generation: int
    state: str
    secret_backend: str = WINDOWS_CREDENTIAL_BACKEND

    def __post_init__(self) -> None:
        if self.version != IDENTITY_VERSION:
            raise ValueError("database identity version is unsupported")
        canonical_installation_uuid(self.installation_uuid)
        expected_scope = derive_installation_scope(self.installation_uuid)
        if (
            not _SCOPE_PATTERN.fullmatch(self.installation_scope)
            or self.installation_scope != expected_scope
        ):
            raise ValueError("database installation UUID and scope disagree")
        if (
            not isinstance(self.secret_generation, int)
            or isinstance(self.secret_generation, bool)
            or self.secret_generation != 1
        ):
            raise ValueError("database secret generation is unsupported")
        if (
            not isinstance(self.secret_handle, str)
            or not _SECRET_HANDLE_PATTERN.fullmatch(self.secret_handle)
            or self.secret_handle
            != f"HADocs/DatabaseIdentity/{self.installation_scope}/{self.secret_generation}"
        ):
            raise ValueError("database secret handle is invalid")
        if self.state != IDENTITY_STATE:
            raise ValueError("database identity state is not initialized")
        if self.secret_backend not in SUPPORTED_CREDENTIAL_BACKENDS:
            raise ValueError("database secret backend is unsupported")

    @classmethod
    def from_mapping(
        cls, config: Mapping[str, object]
    ) -> HaskDatabaseIdentityConfig | None:
        present = tuple(key for key in IDENTITY_CONFIG_KEYS if key in config)
        if not present:
            return None
        legacy_present = tuple(
            key for key in _LEGACY_IDENTITY_CONFIG_KEYS if key in config
        )
        has_backend = "hask_database_secret_backend" in config
        if len(legacy_present) != len(_LEGACY_IDENTITY_CONFIG_KEYS):
            raise ValueError("database identity initialization is partial")
        if not has_backend and os.name != "nt":
            raise ValueError("database identity backend metadata is missing")
        backend = (
            config["hask_database_secret_backend"]
            if has_backend
            else WINDOWS_CREDENTIAL_BACKEND
        )
        return cls(
            version=config[_LEGACY_IDENTITY_CONFIG_KEYS[0]],  # type: ignore[arg-type]
            installation_uuid=config[_LEGACY_IDENTITY_CONFIG_KEYS[1]],  # type: ignore[arg-type]
            installation_scope=config[_LEGACY_IDENTITY_CONFIG_KEYS[2]],  # type: ignore[arg-type]
            secret_handle=config[_LEGACY_IDENTITY_CONFIG_KEYS[3]],  # type: ignore[arg-type]
            secret_generation=config[_LEGACY_IDENTITY_CONFIG_KEYS[4]],  # type: ignore[arg-type]
            state=config[_LEGACY_IDENTITY_CONFIG_KEYS[5]],  # type: ignore[arg-type]
            secret_backend=backend,  # type: ignore[arg-type]
        )

    def as_config_values(self) -> dict[str, object]:
        return {
            "hask_database_identity_version": self.version,
            "hask_database_installation_uuid": self.installation_uuid,
            "hask_database_installation_scope": self.installation_scope,
            "hask_database_secret_handle": self.secret_handle,
            "hask_database_secret_generation": self.secret_generation,
            "hask_database_identity_state": self.state,
            "hask_database_secret_backend": self.secret_backend,
        }


def _environment_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _configuration_bool(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    raise ValueError(f"{name} must be a boolean value")


def _configured_value(
    config: Mapping[str, object], environment_name: str, config_name: str
) -> object | None:
    if environment_name in os.environ:
        return os.environ[environment_name]
    return config.get(config_name)


@dataclass(frozen=True, slots=True)
class HaskDatabaseConfig:
    """Configuration for the isolated HASK operational SQLite boundary."""

    enabled: bool = False
    path: Path | None = None
    busy_timeout_ms: int = 5_000
    expected_user_version: int = 0

    def __post_init__(self) -> None:
        if self.busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be positive")
        if self.expected_user_version < 0:
            raise ValueError("expected_user_version must be non-negative")
        if self.enabled and self.path is None:
            raise ValueError("an explicit local database path is required when enabled")

    @classmethod
    def from_environment(cls) -> HaskDatabaseConfig:
        enabled = _environment_bool("HADOCS_HASK_DATABASE_ENABLED", False)
        raw_path = os.environ.get("HADOCS_HASK_DATABASE_PATH", "").strip()
        path = _runtime_data_path(raw_path) if raw_path else None
        return cls(enabled=enabled, path=path)


@dataclass(frozen=True, slots=True)
class HaskDatabaseApplicationConfig:
    """Explicit product-integration settings layered over database config.

    Normal HADocs configuration remains default-disabled.  Enabling requires
    both a caller-selected SQLite path and a stable, non-secret installation
    reference; neither value is inferred from Home Assistant or the host.
    """

    database: HaskDatabaseConfig
    installation_ref: str | None = None
    identity: HaskDatabaseIdentityConfig | None = None

    def __post_init__(self) -> None:
        if not self.database.enabled:
            return
        if not isinstance(self.installation_ref, str) or not self.installation_ref.strip():
            raise ValueError(
                "an explicit non-secret installation reference is required when enabled"
            )
        reference = self.installation_ref.strip()
        if len(reference) > 256 or any(ord(character) < 32 for character in reference):
            raise ValueError("installation reference must be printable and at most 256 characters")
        if "://" in reference or "/" in reference or "\\" in reference:
            raise ValueError(
                "installation reference must not be a URL or filesystem path"
            )
        if self.database.path is not None and self.database.path.name.lower() == "hudd.sqlite":
            raise ValueError("the operational database must not reuse hudd.sqlite")
        if self.identity is None:
            raise ValueError(
                "database identity must be explicitly initialized before enabling"
            )

    @classmethod
    def from_application_config(
        cls, config: Mapping[str, object] | None
    ) -> HaskDatabaseApplicationConfig:
        values = config or {}
        raw_enabled = _configured_value(
            values,
            "HADOCS_HASK_DATABASE_ENABLED",
            "hask_database_enabled",
        )
        enabled = (
            False
            if raw_enabled is None
            else _configuration_bool(raw_enabled, "hask_database_enabled")
        )
        raw_path = _configured_value(
            values,
            "HADOCS_HASK_DATABASE_PATH",
            "hask_database_path",
        )
        path_text = "" if raw_path is None else str(raw_path).strip()
        path = _runtime_data_path(path_text) if path_text else None
        raw_reference = _configured_value(
            values,
            "HADOCS_HASK_DATABASE_INSTALLATION_REF",
            "hask_database_installation_ref",
        )
        installation_ref = (
            None if raw_reference is None else str(raw_reference).strip() or None
        )
        identity = HaskDatabaseIdentityConfig.from_mapping(values) if enabled else None
        return cls(
            database=HaskDatabaseConfig(enabled=enabled, path=path),
            installation_ref=installation_ref,
            identity=identity,
        )
