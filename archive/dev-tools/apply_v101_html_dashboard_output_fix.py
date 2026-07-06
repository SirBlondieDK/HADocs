from __future__ import annotations

import re
from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")
HOOK = Path("src/hadocs/reports/html_hook.py")

HOOK_TEXT = '"""Compatibility wrapper for the HTML dashboard generator.\n\nImportant:\n- `generate_index(...)` creates the Markdown index.\n- `generate_executive_dashboard(...)` creates `output/index.html`.\n\nThis wrapper keeps older imports working while routing the newer dashboard call\nto the real HTML dashboard generator.\n"""\n\n\ndef generate_html_dashboard(*args, **kwargs):\n    """Generate the HTML dashboard using the appropriate generator."""\n\n    if len(args) >= 10:\n        from src.hadocs.reports.generator import generate_executive_dashboard\n\n        return generate_executive_dashboard(*args, **kwargs)\n\n    if len(args) == 5:\n        from src.hadocs.reports.generator import generate_index\n\n        return generate_index(*args, **kwargs)\n\n    raise TypeError(\n        "generate_html_dashboard expected either 5 legacy args or 10+ dashboard args, "\n        f"got {len(args)}"\n    )\n'


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
    patch_hook()
    patch_generator()

    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Then scan and check:")
    print("  dir output")
    print("")
    print("Expected:")
    print("  output\\index.html")
    print("  output\\index.md")
    print("  output\\explorer\\index.html")
    print("")
    print("Commit:")
    print("  git add -f src/hadocs/reports/html_hook.py src/hadocs/reports/generator.py docs/V101_HTML_DASHBOARD_OUTPUT_FIX.md tools/apply_v101_html_dashboard_output_fix.py")
    print('  git commit -m "Fix HTML dashboard output generation"')
    print("  git push")


if __name__ == "__main__":
    main()
