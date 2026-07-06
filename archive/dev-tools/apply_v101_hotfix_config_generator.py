from __future__ import annotations

import re
from pathlib import Path

CONFIG = Path("src/hadocs/utils/config.py")
GENERATOR = Path("src/hadocs/reports/generator.py")
HOOK = Path("src/hadocs/reports/html_hook.py")

CONFIG_TEXT = 'from __future__ import annotations\n\nimport json\nfrom pathlib import Path\n\nfrom src.hadocs.security.credential_store import (\n    inject_token_into_runtime_config,\n    migrate_plaintext_token_from_config,\n)\n\nCONFIG_FILE = Path("config.json")\n\nDEFAULT_CONFIG = {\n    "ha_url": "http://homeassistant.local:8123",\n    "project_name": "My Smart Home",\n    "output_dir": "output",\n    "cache_dir": "cache",\n    "open_dashboard_after_scan": True,\n}\n\n\ndef config_exists():\n    return CONFIG_FILE.exists()\n\n\ndef load_config():\n    if not CONFIG_FILE.exists():\n        return inject_token_into_runtime_config(DEFAULT_CONFIG)\n\n    try:\n        with CONFIG_FILE.open("r", encoding="utf-8") as f:\n            config = json.load(f)\n    except Exception:\n        return inject_token_into_runtime_config(DEFAULT_CONFIG)\n\n    clean = migrate_plaintext_token_from_config(config or {})\n    if clean != (config or {}):\n        save_config(clean)\n\n    merged = dict(DEFAULT_CONFIG)\n    merged.update(clean or {})\n    return inject_token_into_runtime_config(merged)\n\n\ndef save_config(config):\n    clean = migrate_plaintext_token_from_config(config or {})\n    clean = dict(clean or {})\n    clean.pop("token", None)\n    clean.pop("ha_token", None)\n\n    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)\n    with CONFIG_FILE.open("w", encoding="utf-8") as f:\n        json.dump(clean, f, indent=2)\n\n\ndef validate_config(config):\n    problems = []\n\n    if not config.get("ha_url"):\n        problems.append("Home Assistant URL is missing.")\n\n    if not config.get("token"):\n        problems.append("Home Assistant token is missing.")\n\n    return problems\n'
HOOK_TEXT = '"""Compatibility wrapper for the HTML dashboard generator.\n\nThis module exists for older imports and must avoid circular imports.\n"""\n\n\ndef generate_html_dashboard(*args, **kwargs):\n    """Call generator.generate_index with the argument shape it expects."""\n    from src.hadocs.reports.generator import generate_index\n\n    if len(args) == 5:\n        return generate_index(*args, **kwargs)\n\n    if len(args) >= 8:\n        out = args[0]\n        project_name = args[1]\n        executive = args[3] if len(args) > 3 else {}\n        now = args[-1]\n\n        incidents = []\n        for item in reversed(args[2:-1]):\n            if isinstance(item, list):\n                incidents = item\n                break\n\n        return generate_index(out, project_name, executive, incidents, now)\n\n    return generate_index(*args, **kwargs)\n'


def patch_config():
    if not CONFIG.exists():
        raise SystemExit("Missing src/hadocs/utils/config.py")
    CONFIG.write_text(CONFIG_TEXT, encoding="utf-8")
    print("Rewrote src/hadocs/utils/config.py")


def patch_hook():
    HOOK.parent.mkdir(parents=True, exist_ok=True)
    HOOK.write_text(HOOK_TEXT, encoding="utf-8")
    print("Rewrote src/hadocs/reports/html_hook.py")


def patch_generator():
    if not GENERATOR.exists():
        raise SystemExit("Missing src/hadocs/reports/generator.py")

    text = GENERATOR.read_text(encoding="utf-8")

    if "from src.hadocs.reports.html_hook import generate_html_dashboard" not in text:
        lines = text.splitlines(True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, "from src.hadocs.reports.html_hook import generate_html_dashboard\n")
        text = "".join(lines)

    text = re.sub(
        r"(?<!def )generate_index\(\s*out,\s*project_name,\s*model,\s*executive,",
        "generate_html_dashboard(out, project_name, model, executive,",
        text,
    )

    GENERATOR.write_text(text, encoding="utf-8")
    print("Patched src/hadocs/reports/generator.py")


def main():
    patch_config()
    patch_hook()
    patch_generator()

    print("")
    print("Now run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("After opening Settings and pressing Save, check:")
    print("  cmdkey /list | findstr /i HADocs")
    print("  findstr /i token config.json")
    print("")
    print("Expected:")
    print("  cmdkey finds HADocs/HomeAssistantToken")
    print("  findstr finds nothing")
    print("")
    print("Commit:")
    print("  git add -f src/hadocs/utils/config.py src/hadocs/reports/html_hook.py src/hadocs/reports/generator.py docs/V101_CONFIG_GENERATOR_HOTFIX.md tools/apply_v101_hotfix_config_generator.py")
    print('  git commit -m "Fix credential config and dashboard generator compatibility"')
    print("  git push")


if __name__ == "__main__":
    main()
