from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(".")
ARCHIVE = ROOT / "archive" / "dev-tools"

GITIGNORE_LINES = [
    "# HADocs generated/runtime files",
    "output/",
    "build/",
    "dist/",
    "*.spec",
    "*.toc",
    "*.pyz",
    "*.pkg",
    "xref-*.html",
    "",
    "# Local config/runtime state",
    "config.json",
    "*.log",
    ".pytest_cache/",
    ".pytest_tmp/",
    "__pycache__/",
    "*.py[cod]",
    "",
    "# Release packages",
    "HADocs-*.zip",
    "HADocs-*.exe",
]


def append_gitignore() -> None:
    path = ROOT / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    additions = [line for line in GITIGNORE_LINES if line and line not in existing]

    if additions:
        path.write_text(existing.rstrip() + "\n\n" + "\n".join(additions) + "\n", encoding="utf-8")


def archive_patch_tools() -> None:
    tools = ROOT / "tools"
    if not tools.exists():
        return

    ARCHIVE.mkdir(parents=True, exist_ok=True)

    patterns = ["apply_*.py", "restore_*.py", "*hotfix*.py"]
    for pattern in patterns:
        for item in tools.glob(pattern):
            if item.name == "cleanup_project.py":
                continue
            target = ARCHIVE / item.name
            if target.exists():
                target.unlink()
            shutil.move(str(item), str(target))


def ensure_docs() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    path = docs / "cleanup.md"
    if path.exists():
        return

    path.write_text(
        "# Cleanup Sprint\n\n"
        "This cleanup keeps generated files out of Git and moves temporary patch scripts to `archive/dev-tools/`.\n\n"
        "After applying, run:\n\n"
        "```powershell\n"
        "py -3.14 -m pytest\n"
        "git status\n"
        "```\n\n"
        "If `build/`, `dist/` or `output/` are still tracked:\n\n"
        "```powershell\n"
        "git rm -r --cached build dist output\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> None:
    if not (ROOT / "src" / "hadocs").exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    append_gitignore()
    archive_patch_tools()
    ensure_docs()

    print("Cleanup sprint applied.")
    print("Run: py -3.14 -m pytest")
    print("Run: git status")
    print("If build/dist/output are tracked: git rm -r --cached build dist output")
    print('Commit: git add .gitignore docs/cleanup.md archive/dev-tools tools')
    print('Commit: git commit -m "Clean up project structure"')
    print("Push: git push")


if __name__ == "__main__":
    main()
