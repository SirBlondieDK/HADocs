from __future__ import annotations

from pathlib import Path
import re

ROOTS = [
    Path("src"),
    Path("tests"),
    Path("tools"),
]

TEXT_PATTERNS = [
    ".read_text(",
    ".write_text(",
    "open(",
    "Path(",
]

MOJIBAKE_PATTERNS = [
    "ÔÇö",
    "ÔÇô",
    "ÔÇó",
    "Ô£ô",
    "ÔÜí",
    "Ôÿà",
    "Ôÿå",
    "├ª",
    "├©",
    "├Ñ",
    "├å",
    "├ÿ",
    "├à",
]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    ".venv",
    "venv",
    "output",
}


def iter_files():
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".md", ".txt", ".toml", ".json", ".yml", ".yaml"}:
                continue
            yield path


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def line_hits(text: str, patterns: list[str]):
    for lineno, line in enumerate(text.splitlines(), 1):
        if any(pattern in line for pattern in patterns):
            yield lineno, line.rstrip()


def has_explicit_encoding(line: str) -> bool:
    return "encoding=" in line


def main() -> None:
    report = []
    report.append("# Unicode / Encoding Audit")
    report.append("")
    report.append("This is an audit only. It does not change project files.")
    report.append("")

    text_io_hits = []
    missing_encoding_hits = []
    mojibake_hits = []

    for path in sorted(iter_files()):
        text = read_file(path)

        for lineno, line in line_hits(text, TEXT_PATTERNS):
            text_io_hits.append((path, lineno, line))
            if (".read_text(" in line or ".write_text(" in line or "open(" in line) and not has_explicit_encoding(line):
                missing_encoding_hits.append((path, lineno, line))

        for lineno, line in line_hits(text, MOJIBAKE_PATTERNS):
            mojibake_hits.append((path, lineno, line))

    report.append("## Text IO calls")
    report.append("")
    report.append(f"Found `{len(text_io_hits)}` text/path related lines.")
    report.append("")

    report.append("## Potential missing encoding")
    report.append("")
    if missing_encoding_hits:
        for path, lineno, line in missing_encoding_hits:
            report.append(f"- `{path}:{lineno}` — `{line}`")
    else:
        report.append("No obvious missing `encoding=` calls found.")
    report.append("")

    report.append("## Mojibake patterns in repository")
    report.append("")
    if mojibake_hits:
        for path, lineno, line in mojibake_hits:
            safe_line = line.replace("`", "\\`")
            report.append(f"- `{path}:{lineno}` — `{safe_line}`")
    else:
        report.append("No mojibake patterns found in source/docs/tests/tools.")
    report.append("")

    out = Path("docs/UNICODE_ENCODING_AUDIT.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("Unicode audit complete.")
    print(f"Wrote: {out}")
    print("")
    print("Review:")
    print("  notepad docs\\UNICODE_ENCODING_AUDIT.md")
    print("")
    print("Then run:")
    print("  py -3.14 -m pytest")
    print("")
    print("Commit if useful:")
    print("  git add docs/UNICODE_ENCODING_AUDIT.md tools/audit_unicode_encoding.py")
    print('  git commit -m "Add Unicode encoding audit"')


if __name__ == "__main__":
    main()
