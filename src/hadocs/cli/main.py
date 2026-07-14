import argparse
import sys
from getpass import getpass
from pathlib import Path

from src.hadocs.api.client import HomeAssistantAPI
from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.reports.generator import generate_all
from src.hadocs.utils.config import (
    config_exists,
    load_config,
    save_config,
    validate_config,
    validate_config_warnings,
)
from src.hadocs.utils.security import (
    gitignore_contains_required_entries,
    tracked_generated_files,
    tracked_sensitive_files,
)


def main():
    parser = argparse.ArgumentParser(prog="hadocs", description="Home Assistant Documentation & Analysis")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="Create local configuration")
    sub.add_parser("doctor", help="Run safety and connection checks")
    sub.add_parser("generate", help="Generate documentation and analysis reports")
    sub.add_parser("gui", help="Open the graphical user interface")
    args = parser.parse_args()

    if args.command == "init":
        return cmd_init()
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "generate":
        return cmd_generate()
    if args.command == "gui":
        from src.hadocs.gui.app import run_gui
        run_gui()
        return 0

    parser.print_help()
    return 0


def cmd_init():
    print("HADocs setup")
    print("------------")
    cfg = load_config()
    cfg["ha_url"] = input(f"Home Assistant URL [{cfg['ha_url']}]: ").strip() or cfg["ha_url"]
    cfg["token"] = getpass("Long-Lived Access Token: ").strip()
    cfg["project_name"] = input(f"Project name [{cfg['project_name']}]: ").strip() or cfg["project_name"]
    save_config(cfg)
    print("")
    print("Saved config.json")
    print("Run: hadocs doctor")
    return 0


def cmd_doctor():
    print("HADocs doctor")
    print("-------------")
    ok = True

    if not config_exists():
        print("✗ config.json not found")
        print("  Run: hadocs init")
        return 1

    cfg = load_config()
    problems = validate_config(cfg)
    warnings = validate_config_warnings(cfg)

    for warning in warnings:
        print(f"WARNING: {warning}")

    if problems:
        ok = False
        print("✗ Configuration problems:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("✓ Configuration looks valid")

    try:
        api = HomeAssistantAPI(cfg["ha_url"], cfg["token"])
        api.test_connection()
        print("✓ Home Assistant API reachable")
    except Exception as exc:
        ok = False
        print("✗ Cannot connect to Home Assistant")
        print(f"  {exc}")

    tracked = tracked_sensitive_files()
    if tracked:
        ok = False
        print("✗ Sensitive files are tracked by Git:")
        for file in tracked:
            print(f"  - {file}")
    else:
        print("✓ No sensitive config files tracked by Git")

    generated = tracked_generated_files()
    if generated:
        ok = False
        print("✗ Generated files are tracked by Git:")
        for file in generated:
            print(f"  - {file}")
        print("  Remove with: git rm --cached <file>")
    else:
        print("✓ No generated output files tracked by Git")

    gitignore_ok, missing = gitignore_contains_required_entries()
    if not gitignore_ok:
        ok = False
        print("✗ .gitignore is missing recommended entries:")
        for entry in missing:
            print(f"  - {entry}")
    else:
        print("✓ .gitignore contains safety entries")

    output_dir = Path(cfg.get("output_dir", "output"))
    try:
        output_dir.mkdir(exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        print("✓ Output folder is writable")
    except Exception as exc:
        ok = False
        print("✗ Output folder is not writable")
        print(f"  {exc}")

    print("")
    if ok:
        print("All checks passed.")
        return 0
    print("Some checks failed.")
    return 1


def cmd_generate():
    cfg = load_config()
    problems = validate_config(cfg)
    warnings = validate_config_warnings(cfg)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if problems:
        print("Configuration problems:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    data = collect_all(cfg)
    idx = build_indexes(data)
    generate_all(data, idx, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
