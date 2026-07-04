import json
from pathlib import Path

DEFAULT_CONFIG = {
    "ha_url": "http://192.168.68.129:8123",
    "token": "",
    "project_name": "Det Lille Hjem",
    "output_dir": "output",
    "cache_dir": "cache",
}

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
