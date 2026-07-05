from pathlib import Path
import subprocess

from src.hadocs.utils.config import SENSITIVE_CONFIG_FILES


REQUIRED_GITIGNORE_ENTRIES = [
    "config.json",
    "config.local.json",
    ".env",
    "cache/",
    "output/",
    "*.zip",
]


def is_git_repository(path: str = ".") -> bool:
    return (Path(path) / ".git").exists()


def git_is_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=False)
        return True
    except Exception:
        return False


def git_ls_files(path: str = ".") -> set[str]:
    if not is_git_repository(path) or not git_is_available():
        return set()

    result = subprocess.run(["git", "ls-files"], cwd=path, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return set()

    return set(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())


def tracked_sensitive_files(path: str = ".") -> list[str]:
    tracked = git_ls_files(path)
    return [file for file in SENSITIVE_CONFIG_FILES if file in tracked]


def tracked_generated_files(path: str = ".") -> list[str]:
    tracked = git_ls_files(path)
    generated = []

    for file in tracked:
        low = file.lower()
        if low.startswith("output/") or low.startswith("cache/") or low.startswith("reports/"):
            generated.append(file)
        elif low.endswith(".zip") or low.endswith(".tar") or low.endswith(".tar.gz") or low.endswith(".7z"):
            generated.append(file)

    return sorted(generated)


def gitignore_contains_required_entries(path: str = ".") -> tuple[bool, list[str]]:
    gitignore = Path(path) / ".gitignore"

    if not gitignore.exists():
        return False, REQUIRED_GITIGNORE_ENTRIES

    content = gitignore.read_text(encoding="utf-8", errors="ignore")
    missing = [entry for entry in REQUIRED_GITIGNORE_ENTRIES if entry not in content]
    return len(missing) == 0, missing
