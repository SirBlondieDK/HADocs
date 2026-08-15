from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from hadocs.runtime import RuntimeEnvironment, detect_runtime
from hadocs.security.credential_store import (
    delete_home_assistant_token,
    get_home_assistant_token,
    inject_token_into_runtime_config,
    set_home_assistant_token,
)

from .paths import AppPaths, RuntimeMode


class ConfigPersistenceError(RuntimeError):
    """A redacted configuration persistence failure safe for UI display."""


DEFAULT_CONFIG = {
    "ha_url": "http://homeassistant.local:8123",
    "project_name": "My Smart Home",
    "output_dir": "output",
    "cache_dir": "cache",
    "save_raw_cache": False,
    "open_dashboard_after_scan": True,
    "hask_database_enabled": False,
    "hask_enabled": False,
    "hask_preview_enabled": False,
    "hask_candidate_evidence_enabled": False,
    "hask_native_integration_status_enabled": False,
}

INSECURE_HTTP_WARNING = (
    "Long-Lived Access Tokens are transmitted in plaintext over HTTP. "
    "HTTPS is strongly recommended unless you are connecting to localhost."
)

SENSITIVE_CONFIG_FILES = [
    "config.json",
    "local-config.json",
    ".env",
]


def resolve_config_file(paths: AppPaths | None = None) -> Path:
    """Resolve the active configuration file while supporting legacy installs."""
    app_paths = paths or AppPaths.discover()
    configured_path = os.environ.get("HADOCS_CONFIG_FILE")

    if configured_path:
        return app_paths.resolve_data_path(configured_path)

    if (
        app_paths.mode is not RuntimeMode.WINDOWS_INSTALLED
        and app_paths.legacy_config_file.exists()
        and not app_paths.config_file.exists()
    ):
        return app_paths.legacy_config_file

    return app_paths.config_file


class ConfigManager:
    """Own loading, saving, overriding, and validating HADocs configuration."""

    def __init__(
        self,
        *,
        paths: AppPaths | None = None,
        config_file: Path | str | None = None,
    ) -> None:
        self.paths = paths or AppPaths.discover()
        self.config_file = (
            self.paths.resolve_data_path(config_file)
            if config_file is not None
            else resolve_config_file(self.paths)
        )

    def apply_environment_overrides(self, config: dict | None) -> dict:
        """Apply optional HADOCS_* environment variables."""
        result = dict(config or {})

        text_mapping = {
            "HADOCS_HA_URL": "ha_url",
            "HADOCS_OUTPUT_DIR": "output_dir",
            "HADOCS_CACHE_DIR": "cache_dir",
            "HADOCS_PROJECT_NAME": "project_name",
            "HADOCS_HASK_DATABASE_PATH": "hask_database_path",
            "HADOCS_HASK_DATABASE_INSTALLATION_REF": (
                "hask_database_installation_ref"
            ),
            "HADOCS_HASK_DATABASE_SECRET_BACKEND": (
                "hask_database_secret_backend"
            ),
            "HADOCS_HASK_CREDENTIAL_STORE_PATH": (
                "hask_database_credential_store_path"
            ),
            "HADOCS_HASK_BUNDLE_PATH": "hask_bundle_path",
        }

        for environment_name, config_name in text_mapping.items():
            value = os.environ.get(environment_name)
            if value:
                result[config_name] = value.strip()

        boolean_mapping = {
            "HADOCS_HASK_DATABASE_ENABLED": "hask_database_enabled",
            "HADOCS_HASK_ENABLED": "hask_enabled",
            "HADOCS_HASK_PREVIEW_ENABLED": "hask_preview_enabled",
            "HADOCS_HASK_CANDIDATE_EVIDENCE_ENABLED": (
                "hask_candidate_evidence_enabled"
            ),
            "HADOCS_HASK_NATIVE_INTEGRATION_STATUS_ENABLED": (
                "hask_native_integration_status_enabled"
            ),
        }
        for environment_name, config_name in boolean_mapping.items():
            value = os.environ.get(environment_name)
            if value is None:
                continue
            normalized = value.strip().casefold()
            if normalized in {"1", "true", "yes", "on"}:
                result[config_name] = True
            elif normalized in {"0", "false", "no", "off", ""}:
                result[config_name] = False
            else:
                raise ValueError(
                    f"{environment_name} must be a boolean value"
                )

        token = os.environ.get("HADOCS_TOKEN")
        if token:
            result["token"] = token.strip()

        return result

    def apply_runtime_overrides(self, config: dict | None) -> dict:
        """Apply values that are mandatory for the detected runtime."""
        result = dict(config or {})
        runtime = detect_runtime()

        if runtime is RuntimeEnvironment.HOME_ASSISTANT_ADDON:
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "").strip()

            result["ha_url"] = "http://supervisor/core"

            if supervisor_token:
                result["token"] = supervisor_token

        return result

    def exists(self) -> bool:
        """Return True when a usable configuration source is available."""
        runtime = detect_runtime()

        if runtime is RuntimeEnvironment.HOME_ASSISTANT_ADDON:
            return bool(os.environ.get("SUPERVISOR_TOKEN", "").strip())

        if self.config_file.exists():
            return True

        return bool(
            os.environ.get("HADOCS_HA_URL", "").strip()
            and os.environ.get("HADOCS_TOKEN", "").strip()
        )

    def load(self) -> dict:
        """Load and merge configuration for the current runtime."""
        if self.config_file.exists():
            try:
                with self.config_file.open("r", encoding="utf-8") as file:
                    stored_config = json.load(file)
            except (OSError, json.JSONDecodeError):
                stored_config = {}
        else:
            stored_config = {}

        clean_config = dict(stored_config or {})
        if any(key in clean_config for key in ("token", "ha_token")):
            # Save performs the credential/config update as one recoverable
            # operation and removes the plaintext token from disk.
            self.save(clean_config)
            clean_config.pop("token", None)
            clean_config.pop("ha_token", None)

        merged = dict(DEFAULT_CONFIG)
        merged.update(clean_config or {})

        merged = inject_token_into_runtime_config(merged)
        merged = self.apply_environment_overrides(merged)
        merged = self.apply_runtime_overrides(merged)
        merged = self.resolve_runtime_paths(merged)

        return merged

    def save(self, config: dict | None) -> None:
        """Atomically save config and recover credential changes on failure."""

        clean = dict(config or {})
        token_value = clean.pop("token", None) or clean.pop("ha_token", None)
        token = str(token_value) if token_value else None
        temporary = self.config_file.with_name(
            f".{self.config_file.name}.hadocs-save-{uuid4().hex}.tmp"
        )
        previous_token: str | None = None
        credential_changed = False

        try:
            # Creating and flushing the temporary file proves the runtime root
            # is writable before Windows Credential Manager is changed.
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("x", encoding="utf-8") as file:
                json.dump(clean, file, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            if token:
                previous_token = get_home_assistant_token()
                if token != previous_token:
                    credential_changed = bool(set_home_assistant_token(token))

            os.replace(temporary, self.config_file)
        except Exception as error:
            if credential_changed:
                try:
                    if previous_token:
                        set_home_assistant_token(previous_token)
                    else:
                        delete_home_assistant_token()
                except Exception:
                    pass
            raise ConfigPersistenceError(
                "HADocs could not save configuration in the selected data "
                "directory. Check folder permissions and available disk space."
            ) from error
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def resolve_runtime_paths(self, config: dict | None) -> dict:
        """Resolve mutable relative paths against the writable data root."""

        result = dict(config or {})
        for key in (
            "output_dir",
            "cache_dir",
            "logs_dir",
            "hask_database_path",
            "hask_database_credential_store_path",
        ):
            value = result.get(key)
            if isinstance(value, (str, Path)) and str(value).strip():
                result[key] = str(self.paths.resolve_data_path(value))

        bundle = result.get("hask_bundle_path")
        if isinstance(bundle, (str, Path)) and str(bundle).strip():
            result["hask_bundle_path"] = str(
                self.paths.resolve_resource_path(bundle)
            )
        return result

    def validate(self, config: dict) -> list[str]:
        """Return blocking configuration problems."""
        problems: list[str] = []

        ha_url = (config.get("ha_url") or "").strip()
        token = (config.get("token") or "").strip()

        if not ha_url:
            problems.append("Home Assistant URL is missing.")
        elif not ha_url.startswith(("http://", "https://")):
            problems.append(
                "Home Assistant URL must start with http:// or https://."
            )

        if not token:
            problems.append("Token is missing.")

        return problems

    def validate_warnings(self, config: dict) -> list[str]:
        """Return non-blocking configuration warnings."""
        warnings: list[str] = []

        ha_url = (config.get("ha_url") or "").strip()
        token = (config.get("token") or "").strip()

        if not ha_url or not token:
            return warnings

        try:
            parsed = urlparse(ha_url)
        except ValueError:
            return warnings

        hostname = (parsed.hostname or "").lower()
        internal_hosts = {
            "localhost",
            "127.0.0.1",
            "::1",
            "supervisor",
        }

        if parsed.scheme.lower() == "http" and hostname not in internal_hosts:
            warnings.append(INSECURE_HTTP_WARNING)

        return warnings
