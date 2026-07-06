from __future__ import annotations

import json
from pathlib import Path

from src.hadocs.security.credential_store import (
    inject_token_into_runtime_config,
    migrate_plaintext_token_from_config,
)

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "ha_url": "http://homeassistant.local:8123",
    "project_name": "My Smart Home",
    "output_dir": "output",
    "cache_dir": "cache",
    "open_dashboard_after_scan": True,
}


def config_exists():
    return CONFIG_FILE.exists()


def load_config():
    if not CONFIG_FILE.exists():
        return inject_token_into_runtime_config(DEFAULT_CONFIG)

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
    return inject_token_into_runtime_config(merged)


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


SENSITIVE_CONFIG_FILES = [
    "config.json",
    "local-config.json",
    ".env",
]
