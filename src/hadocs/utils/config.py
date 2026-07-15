from __future__ import annotations

import os
import json
from pathlib import Path
from urllib.parse import urlparse

from src.hadocs.security.credential_store import (
    inject_token_into_runtime_config,
    migrate_plaintext_token_from_config,
)

CONFIG_FILE = Path(
    os.environ.get("HADOCS_CONFIG_FILE", "config.json")
).expanduser()

DEFAULT_CONFIG = {
    "ha_url": "http://homeassistant.local:8123",
    "project_name": "My Smart Home",
    "output_dir": "output",
    "cache_dir": "cache",
    "save_raw_cache": False,
    "open_dashboard_after_scan": True,
}

def apply_environment_overrides(config):
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

def config_exists():
    return CONFIG_FILE.exists()


def load_config():
    if not CONFIG_FILE.exists():
        return apply_environment_overrides(
            inject_token_into_runtime_config(DEFAULT_CONFIG)
)

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return inject_token_into_runtime_config(DEFAULT_CONFIG)

    clean = migrate_plaintext_token_from_config(config or {})
    if clean != (config or {}):
        save_config(clean)

    merged = dict(DEFAULT_CONFIG)
    merged.update(clean or {})
    return apply_environment_overrides(
        inject_token_into_runtime_config(merged)
)


def save_config(config):
    clean = migrate_plaintext_token_from_config(config or {})
    clean = dict(clean or {})
    clean.pop("token", None)
    clean.pop("ha_token", None)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)


def validate_config(config):
    problems = []

    ha_url = (config.get("ha_url") or "").strip()
    token = (config.get("token") or "").strip()

    if not ha_url:
        problems.append("Home Assistant URL is missing.")
    elif not ha_url.startswith(("http://", "https://")):
        problems.append("Home Assistant URL must start with http:// or https://.")

    if not token:
        problems.append("Token is missing.")

    return problems


INSECURE_HTTP_WARNING = (
    "Long-Lived Access Tokens are transmitted in plaintext over HTTP. "
    "HTTPS is strongly recommended unless you are connecting to localhost."
)


def validate_config_warnings(config):
    warnings = []

    ha_url = (config.get("ha_url") or "").strip()
    token = (config.get("token") or "").strip()

    if not ha_url or not token:
        return warnings

    try:
        parsed = urlparse(ha_url)
    except ValueError:
        return warnings

    hostname = (parsed.hostname or "").lower()

    if parsed.scheme.lower() == "http" and hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        warnings.append(INSECURE_HTTP_WARNING)

    return warnings


SENSITIVE_CONFIG_FILES = [
    "config.json",
    "local-config.json",
    ".env",
]
