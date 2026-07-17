from __future__ import annotations

from pathlib import Path

from src.hadocs.platform.config_manager import (
    DEFAULT_CONFIG,
    INSECURE_HTTP_WARNING,
    SENSITIVE_CONFIG_FILES,
    ConfigManager,
    resolve_config_file,
)


CONFIG_FILE = resolve_config_file()


def _manager() -> ConfigManager:
    """Create a manager using the currently configured compatibility path."""
    return ConfigManager(config_file=CONFIG_FILE)


def apply_environment_overrides(config: dict | None) -> dict:
    """Apply optional HADOCS_* environment variables."""
    return _manager().apply_environment_overrides(config)


def apply_runtime_overrides(config: dict | None) -> dict:
    """Apply values that are mandatory for the detected runtime."""
    return _manager().apply_runtime_overrides(config)


def config_exists() -> bool:
    """Return True when a usable configuration source is available."""
    return _manager().exists()


def load_config() -> dict:
    """Load and merge configuration for the current runtime."""
    return _manager().load()


def save_config(config: dict | None) -> None:
    """Save non-sensitive configuration values."""
    _manager().save(config)


def validate_config(config: dict) -> list[str]:
    """Return blocking configuration problems."""
    return _manager().validate(config)


def validate_config_warnings(config: dict) -> list[str]:
    """Return non-blocking configuration warnings."""
    return _manager().validate_warnings(config)
