from pathlib import Path

HOOK = Path("src/hadocs/reports/html_hook.py")

HOOK_TEXT = '"""Compatibility wrapper for the HTML dashboard generator.\n\n`generate_index(...)` creates the Markdown index.\n`generate_executive_dashboard(...)` creates `output/index.html`.\n\nThis wrapper accepts both old and new call shapes so GUI/report code can stay\ncompatible while the generator API is cleaned up.\n"""\n\n\ndef generate_html_dashboard(*args, **kwargs):\n    """Generate HTML dashboard or legacy markdown index."""\n\n    if len(args) == 5:\n        from src.hadocs.reports.generator import generate_index\n\n        return generate_index(*args, **kwargs)\n\n    if len(args) >= 8:\n        from src.hadocs.reports.generator import generate_executive_dashboard\n\n        out = args[0]\n        project_name = args[1]\n        model = args[2]\n        executive = args[3]\n        health_notes = args[4]\n        history_comparison = args[5]\n        trend_summary = args[6]\n\n        if len(args) == 8:\n            incidents = []\n            raw_incidents = []\n            now = args[7]\n        elif len(args) == 9:\n            incidents = args[7]\n            raw_incidents = []\n            now = args[8]\n        else:\n            incidents = args[7]\n            raw_incidents = args[8]\n            now = args[9]\n\n        return generate_executive_dashboard(\n            out,\n            project_name,\n            model,\n            executive,\n            health_notes,\n            history_comparison,\n            trend_summary,\n            incidents,\n            raw_incidents,\n            now,\n        )\n\n    raise TypeError(\n        "generate_html_dashboard expected 5 legacy args or 8+ dashboard args, "\n        f"got {len(args)}"\n    )\n'


def main():
    HOOK.parent.mkdir(parents=True, exist_ok=True)
    HOOK.write_text(HOOK_TEXT, encoding="utf-8")

    print("Patched html_hook.py to accept 8, 9 and 10 argument dashboard calls.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("After scan:")
    print("  dir output")
    print("")
    print("Expected:")
    print("  index.html")
    print("  index.md")
    print("")
    print("Commit:")
    print("  git add -f src/hadocs/reports/html_hook.py docs/V101_HTML_WRAPPER_8ARG_FIX.md tools/apply_v101_html_wrapper_8arg_fix.py")
    print('  git commit -m "Fix HTML dashboard wrapper argument compatibility"')
    print("  git push")


if __name__ == "__main__":
    main()
