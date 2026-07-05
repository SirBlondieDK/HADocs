import json
from pathlib import Path


DEFAULT_CONFIG = {
    "ha_url": "http://homeassistant.local:8123",
    "token": "",
    "project_name": "My Smart Home",
    "output_dir": "output",
    "cache_dir": "cache",
}

SENSITIVE_CONFIG_FILES = ["config.json", "config.local.json", ".env"]
GENERATED_PATHS = ["cache", "output", "reports"]
GENERATED_ARCHIVE_PATTERNS = [".zip", ".tar", ".tar.gz", ".7z"]


def load_config(path: str = "config.json") -> dict:
    cfg_path = Path(path)
    if not cfg_path.exists():
        return dict(DEFAULT_CONFIG)
    loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(loaded)
    return cfg


def save_config(cfg: dict, path: str = "config.json") -> None:
    Path(path).write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def config_exists(path: str = "config.json") -> bool:
    return Path(path).exists()


def validate_config(cfg: dict) -> list[str]:
    problems = []

    url = (cfg.get("ha_url") or "").strip()
    token = (cfg.get("token") or "").strip()

    if not url:
        problems.append("Home Assistant URL is missing.")
    elif not (url.startswith("http://") or url.startswith("https://")):
        problems.append("Home Assistant URL must start with http:// or https://.")

    if not token:
        problems.append("Long-Lived Access Token is missing.")
    elif token == "INDSÆT_DIN_LONG_LIVED_ACCESS_TOKEN_HER":
        problems.append("Token still contains the placeholder value.")

    if not cfg.get("output_dir"):
        problems.append("output_dir is missing.")

    if not cfg.get("cache_dir"):
        problems.append("cache_dir is missing.")

    return problems
