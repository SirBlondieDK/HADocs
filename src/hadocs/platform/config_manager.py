from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from src.hadocs.runtime import RuntimeEnvironment, detect_runtime
from src.hadocs.security.credential_store import (
    inject_token_into_runtime_config,
    migrate_plaintext_token_from_config,
)

from .paths import AppPaths


DEFAULT_CONFIG = {
    "ha_url": "http://homeassistant.local:8123",
    "project_name": "My Smart Home",
    "output_dir": "output",
    "cache_dir": "cache",
    "save_raw_cache": False,
    "open_dashboard_after_scan": True,
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
    configured_path = os.environ.get("HADOCS_CONFIG_FILE")

    if configured_path:
        return Path(configured_path).expanduser()

    app_paths = paths or AppPaths.discover()

    if (
        app_paths.legacy_config_file.exists()
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
            Path(config_file).expanduser()
            if config_file is not None
            else resolve_config_file(self.paths)
        )

    def apply_environment_overrides(self, config: dict | None) -> dict:
        """Apply optional HADOCS_* environment variables."""
        result = dict(config or {})

        mapping = {
            "HADOCS_HA_URL": "ha_url",
            "HADOCS_OUTPUT_DIR": "output_dir",
            "HADOCS_CACHE_DIR": "cache_dir",
            "HADOCS_PROJECT_NAME": "project_name",
        }

        for environment_name, config_name in mapping.items():
            value = os.environ.get(environment_name)
            if value:
                result[config_name] = value.strip()

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

        clean_config = migrate_plaintext_token_from_config(stored_config or {})

        if clean_config != (stored_config or {}) and self.config_file.exists():
            self.save(clean_config)

        merged = dict(DEFAULT_CONFIG)
        merged.update(clean_config or {})

        merged = inject_token_into_runtime_config(merged)
        merged = self.apply_environment_overrides(merged)
        merged = self.apply_runtime_overrides(merged)

        return merged

    def save(self, config: dict | None) -> None:
        """Save non-sensitive configuration values."""
        clean = migrate_plaintext_token_from_config(config or {})
        clean = dict(clean or {})

        clean.pop("token", None)
        clean.pop("ha_token", None)

        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with self.config_file.open("w", encoding="utf-8") as file:
            json.dump(clean, file, indent=2)

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
