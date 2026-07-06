
from __future__ import annotations

import re
import subprocess
from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")

# This is the commit from your log:
# 8613b14 Polish desktop GUI final tweaks
KNOWN_GOOD_COMMITS = [
    "8613b14",
    "e2b9f16",
    "9224d2b",
]


def run_git_show(commit: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:src/hadocs/reports/generator.py"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except Exception:
        return None


def extract_function(source: str, name: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\([^)]*\):\n", source, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find function {name}")

    start = match.start()
    next_def = re.search(r"^def [A-Za-z_][A-Za-z0-9_]*\(", source[match.end():], flags=re.MULTILINE)
    if not next_def:
        return source[start:].rstrip() + "\n"

    end = match.end() + next_def.start()
    return source[start:end].rstrip() + "\n"


def replace_function(source: str, name: str, replacement: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\([^)]*\):\n", source, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find current function {name}")

    start = match.start()
    next_def = re.search(r"^def [A-Za-z_][A-Za-z0-9_]*\(", source[match.end():], flags=re.MULTILINE)
    end = match.end() + next_def.start() if next_def else len(source)

    return source[:start] + replacement.rstrip() + "\n\n" + source[end:].lstrip("\n")


def remove_html_hook_usage(source: str) -> str:
    source = source.replace("from src.hadocs.reports.html_hook import generate_html_dashboard\n", "")

    # Remove a standalone generate_html_dashboard(...) call block inside generate_all,
    # if one of the previous compatibility patches inserted it.
    lines = source.splitlines(True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("    generate_html_dashboard("):
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            continue
        out.append(line)
        i += 1

    return "".join(out)


def ensure_dashboard_call(source: str) -> str:
    if "generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)" in source:
        return source

    needle = "generate_index(out, project_name, executive, incidents, now)\n"
    call = "generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)\n"

    if needle not in source:
        raise RuntimeError("Could not find generate_index call in generate_all")

    return source.replace(needle, needle + call, 1)


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run from the HADocs repository root.")

    old_source = None
    used_commit = None

    for commit in KNOWN_GOOD_COMMITS:
        candidate = run_git_show(commit)
        if candidate and "def generate_executive_dashboard" in candidate and "index.html" in candidate:
            old_source = candidate
            used_commit = commit
            break

    if not old_source:
        raise SystemExit(
            "Could not find an older generator.py with index.html in the known commits. "
            "Run: git log --oneline -- src/hadocs/reports/generator.py"
        )

    old_dashboard = extract_function(old_source, "generate_executive_dashboard")

    current = GENERATOR.read_text(encoding="utf-8")
    current = remove_html_hook_usage(current)
    current = replace_function(current, "generate_executive_dashboard", old_dashboard)
    current = ensure_dashboard_call(current)

    GENERATOR.write_text(current, encoding="utf-8")

    print(f"Restored professional HTML dashboard from commit {used_commit}.")
    print("Removed internal html_hook wrapper usage from generator.py.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("After scan:")
    print("  dir output\\index.html")
    print("")
    print("Expected:")
    print("  output\\index.html exists and looks like the previous professional dashboard.")
    print("")
    print("If everything works:")
    print("  git add src/hadocs/reports/generator.py docs/V101_RESTORE_PROFESSIONAL_DASHBOARD.md tools/restore_professional_dashboard.py")
    print('  git commit -m "Restore professional HTML dashboard generation"')
    print("  git push")


if __name__ == "__main__":
    main()
