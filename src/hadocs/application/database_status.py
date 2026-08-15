from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3

from hadocs.application.operational_database import (
    DatabaseIdentityInitializationResult,
    initialize_operational_database_identity,
)


_APPLICATION_ID = 0x4841534B
_COUNT_TABLES = {
    "installations": "logical_installation",
    "scans": "scan_run",
    "observations": "observation",
    "entities": "entity",
    "relationships": "relationship",
}
_LIMITATION = "controller/API connection result deferred"
_SUPPORTED_BACKENDS = frozenset({"windows_credential_manager", "posix_file"})


@dataclass(frozen=True, slots=True)
class OperationalDatabaseStatus:
    enabled: bool
    identity_initialized: bool
    protected_backend: str
    protected_material_valid: bool
    database_file_present: bool
    schema_version: int | None
    integrity_status: str
    foreign_key_status: str
    counts: Mapping[str, int | None]
    hask_enabled: bool
    candidate_bridge_enabled: bool
    native_domain_status_enabled: bool
    limitation: str = _LIMITATION

    def lines(self) -> tuple[str, ...]:
        yes_no = lambda value: "yes" if value else "no"
        version = "not available" if self.schema_version is None else str(self.schema_version)
        lines = [
            f"Operational database enabled: {yes_no(self.enabled)}",
            f"Identity initialized: {yes_no(self.identity_initialized)}",
            f"Protected backend kind: {self.protected_backend}",
            (
                "Protected material accessible/valid: "
                f"{yes_no(self.protected_material_valid)}"
            ),
            f"Database file present: {yes_no(self.database_file_present)}",
            f"Schema version: {version}",
            f"Integrity status: {self.integrity_status}",
            f"Foreign-key status: {self.foreign_key_status}",
        ]
        for name in _COUNT_TABLES:
            value = self.counts.get(name)
            rendered = "not available" if value is None else str(value)
            lines.append(f"{name.capitalize()}: {rendered}")
        lines.extend(
            (
                f"HASK enabled: {yes_no(self.hask_enabled)}",
                f"Candidate bridge enabled: {yes_no(self.candidate_bridge_enabled)}",
                (
                    "Native domain status enabled: "
                    f"{yes_no(self.native_domain_status_enabled)}"
                ),
                f"Current conservative limitation: {self.limitation}",
            )
        )
        return tuple(lines)


def initialize_database_identity(
    config: Mapping[str, object],
    *,
    secret_provider: object | None = None,
    uuid_factory: Callable[[], object] | None = None,
    save: Callable[[dict[str, object]], None] | None = None,
) -> tuple[DatabaseIdentityInitializationResult, dict[str, object]]:
    """Shared explicit initialization entry point for CLI and GUI."""

    kwargs: dict[str, object] = {
        "secret_provider": secret_provider,
        "save": save,
    }
    if uuid_factory is not None:
        kwargs["uuid_factory"] = uuid_factory
    return initialize_operational_database_identity(config, **kwargs)


def read_operational_database_status(
    config: Mapping[str, object],
    *,
    secret_provider: object | None = None,
) -> OperationalDatabaseStatus:
    """Inspect configured state without creating, migrating, or mutating it."""

    enabled = _safe_boolean(
        config, "HADOCS_HASK_DATABASE_ENABLED", "hask_database_enabled"
    )
    hask_enabled = _safe_boolean(config, "HADOCS_HASK_ENABLED", "hask_enabled")
    candidate_enabled = _safe_boolean(
        config,
        "HADOCS_HASK_CANDIDATE_EVIDENCE_ENABLED",
        "hask_candidate_evidence_enabled",
    )
    native_enabled = _safe_boolean(
        config,
        "HADOCS_HASK_NATIVE_INTEGRATION_STATUS_ENABLED",
        "hask_native_integration_status_enabled",
    )

    identity = None
    try:
        from hadocs.hask_database import HaskDatabaseIdentityConfig

        identity = HaskDatabaseIdentityConfig.from_mapping(config)
    except (TypeError, ValueError):
        identity = None

    configured_backend = _configured_text(
        config,
        "HADOCS_HASK_DATABASE_SECRET_BACKEND",
        "hask_database_secret_backend",
    )
    backend = identity.secret_backend if identity is not None else configured_backend
    safe_backend = backend if backend in _SUPPORTED_BACKENDS else "not configured"
    protected_valid = False
    if identity is not None:
        try:
            from hadocs.application.operational_database import operational_secret_provider
            from hadocs.hask_database import SecretState

            provider = operational_secret_provider(
                config,
                identity_backend=identity.secret_backend,
                injected=secret_provider,
            )
            protected_valid = (
                provider.validate(identity.secret_handle, identity.secret_generation).state
                is SecretState.AVAILABLE
            )
        except Exception:
            protected_valid = False

    path_text = _configured_text(
        config, "HADOCS_HASK_DATABASE_PATH", "hask_database_path"
    )
    if path_text:
        from hadocs.platform.paths import AppPaths

        path = AppPaths.discover().resolve_data_path(path_text)
    else:
        path = None
    present = bool(path is not None and path.is_file())
    schema_version: int | None = None
    integrity_status = "not available"
    foreign_key_status = "not available"
    counts: dict[str, int | None] = {name: None for name in _COUNT_TABLES}

    if present and path is not None:
        try:
            uri = f"{path.resolve().as_uri()}?mode=ro&immutable=1"
            connection = sqlite3.connect(uri, uri=True, isolation_level=None)
            try:
                connection.execute("PRAGMA query_only = ON")
                application_id = int(
                    connection.execute("PRAGMA application_id").fetchone()[0]
                )
                schema_version = int(
                    connection.execute("PRAGMA user_version").fetchone()[0]
                )
                if application_id != _APPLICATION_ID:
                    integrity_status = "unexpected application"
                    foreign_key_status = "not available"
                else:
                    integrity_rows = connection.execute(
                        "PRAGMA integrity_check"
                    ).fetchall()
                    integrity_status = (
                        "ok"
                        if tuple(str(row[0]) for row in integrity_rows) == ("ok",)
                        else "failed"
                    )
                    foreign_key_status = (
                        "ok"
                        if not connection.execute("PRAGMA foreign_key_check").fetchone()
                        else "failed"
                    )
                    tables = {
                        str(row[0])
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master WHERE type = 'table'"
                        )
                    }
                    for name, table in _COUNT_TABLES.items():
                        if table in tables:
                            counts[name] = int(
                                connection.execute(
                                    f'SELECT COUNT(*) FROM "{table}"'
                                ).fetchone()[0]
                            )
            finally:
                connection.close()
        except (OSError, sqlite3.Error, TypeError, ValueError):
            schema_version = None
            integrity_status = "unavailable"
            foreign_key_status = "unavailable"
            counts = {name: None for name in _COUNT_TABLES}

    return OperationalDatabaseStatus(
        enabled=enabled,
        identity_initialized=identity is not None,
        protected_backend=safe_backend,
        protected_material_valid=protected_valid,
        database_file_present=present,
        schema_version=schema_version,
        integrity_status=integrity_status,
        foreign_key_status=foreign_key_status,
        counts=counts,
        hask_enabled=hask_enabled,
        candidate_bridge_enabled=candidate_enabled,
        native_domain_status_enabled=native_enabled,
    )


def _configured_text(
    config: Mapping[str, object], environment_name: str, config_name: str
) -> str:
    raw = os.environ.get(environment_name, config.get(config_name, ""))
    return "" if raw is None else str(raw).strip()


def _safe_boolean(
    config: Mapping[str, object], environment_name: str, config_name: str
) -> bool:
    value = os.environ.get(environment_name, config.get(config_name, False))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    return False
