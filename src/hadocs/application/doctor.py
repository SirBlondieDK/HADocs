from __future__ import annotations

from pathlib import Path

from src.hadocs.providers import HomeAssistantProvider
from src.hadocs.utils.config import (
    config_exists,
    load_config,
    validate_config,
    validate_config_warnings,
)
from src.hadocs.utils.security import (
    gitignore_contains_required_entries,
    is_git_repository,
    tracked_generated_files,
    tracked_sensitive_files,
)


class DoctorApplication:
    """Run HADocs configuration, connection, and safety checks."""

    def run(self) -> int:
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
            provider = HomeAssistantProvider.from_config(cfg)
            provider.test_connection()
            print("✓ Home Assistant API reachable")
        except Exception as exc:
            ok = False
            print("✗ Cannot connect to Home Assistant")
            print(f"  {exc}")

        if is_git_repository():
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
        else:
            print("✓ Git repository checks skipped (running outside a Git checkout)")

        output_dir = Path(cfg.get("output_dir", "output"))

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
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
