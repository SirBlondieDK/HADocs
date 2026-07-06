from pathlib import Path

HOOK = Path("src/hadocs/reports/html_hook.py")

HOOK_TEXT = '"""Compatibility wrapper for the HTML dashboard generator.\n\nThis module bridges old/new internal generator call shapes.\n\nImportant:\n- generate_index(...) creates output/index.md\n- generate_executive_dashboard(...) creates output/index.html\n"""\n\n\ndef _default_model():\n    return {\n        "areas": [],\n        "devices": [],\n        "entities": [],\n        "integrations": [],\n        "services": [],\n        "config": {},\n    }\n\n\ndef _as_dict(value):\n    return value if isinstance(value, dict) else {}\n\n\ndef _as_list(value):\n    return value if isinstance(value, list) else []\n\n\ndef generate_html_dashboard(*args, **kwargs):\n    """Generate HTML dashboard while accepting legacy argument shapes."""\n\n    if len(args) == 5:\n        from src.hadocs.reports.generator import generate_index\n\n        return generate_index(*args, **kwargs)\n\n    from src.hadocs.reports.generator import generate_executive_dashboard\n\n    if len(args) == 8:\n        # Current HADocs call shape after the GUI/report refactors:\n        # out, project_name, executive, health_notes,\n        # history_comparison, trend_summary, incidents, now\n        out, project_name, executive, health_notes, history_comparison, trend_summary, incidents, now = args\n        return generate_executive_dashboard(\n            out,\n            project_name,\n            _default_model(),\n            _as_dict(executive),\n            health_notes,\n            _as_dict(history_comparison),\n            _as_dict(trend_summary),\n            _as_list(incidents),\n            _as_list(incidents),\n            now,\n        )\n\n    if len(args) == 9:\n        # out, project_name, model, executive, health_notes,\n        # history_comparison, trend_summary, incidents, now\n        out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, now = args\n        return generate_executive_dashboard(\n            out,\n            project_name,\n            _as_dict(model) or _default_model(),\n            _as_dict(executive),\n            health_notes,\n            _as_dict(history_comparison),\n            _as_dict(trend_summary),\n            _as_list(incidents),\n            _as_list(incidents),\n            now,\n        )\n\n    if len(args) >= 10:\n        # Full modern call:\n        # out, project_name, model, executive, health_notes,\n        # history_comparison, trend_summary, incidents, raw_incidents, now\n        out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now = args[:10]\n        return generate_executive_dashboard(\n            out,\n            project_name,\n            _as_dict(model) or _default_model(),\n            _as_dict(executive),\n            health_notes,\n            _as_dict(history_comparison),\n            _as_dict(trend_summary),\n            _as_list(incidents),\n            _as_list(raw_incidents),\n            now,\n        )\n\n    raise TypeError(\n        "generate_html_dashboard expected 5, 8, 9 or 10+ args, "\n        f"got {len(args)}"\n    )\n'


def main():
    HOOK.parent.mkdir(parents=True, exist_ok=True)
    HOOK.write_text(HOOK_TEXT, encoding="utf-8")

    print("Final dashboard wrapper fix applied.")
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
    print("  git add -f src/hadocs/reports/html_hook.py docs/V101_FINAL_DASHBOARD_WRAPPER_FIX.md tools/apply_v101_final_dashboard_wrapper_fix.py")
    print('  git commit -m "Fix dashboard generator argument mapping"')
    print("  git push")


if __name__ == "__main__":
    main()
