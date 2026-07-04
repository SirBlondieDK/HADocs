import re
from pathlib import Path

def slugify(value: str) -> str:
    value = (value or "uden_navn").strip().lower()
    value = value.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "uden_navn"

def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

def safe(value, default: str = "") -> str:
    return default if value is None else str(value)
