from pathlib import Path
import subprocess

from src.hadocs.utils.config import SENSITIVE_CONFIG_FILES


def is_git_repository(path: str = ".") -> bool:
    return (Path(path) / ".git").exists()


def git_is_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=False)
        return True
    except Exception:
        return False


def tracked_sensitive_files(path: str = ".") -> list[str]:
    if not is_git_repository(path) or not git_is_available():
        return []

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return []

    tracked = set(line.strip() for line in result.stdout.splitlines() if line.strip())
    return [file for file in SENSITIVE_CONFIG_FILES if file in tracked]


def gitignore_contains_required_entries(path: str = ".") -> tuple[bool, list[str]]:
    gitignore = Path(path) / ".gitignore"
    required = ["config.json", "config.local.json", ".env", "cache/", "output/"]

    if not gitignore.exists():
        return False, required

    content = gitignore.read_text(encoding="utf-8", errors="ignore")
    missing = [entry for entry in required if entry not in content]
    return len(missing) == 0, missing
