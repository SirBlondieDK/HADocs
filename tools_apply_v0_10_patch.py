from pathlib import Path

GEN = Path("src/hadocs/reports/generator.py")
IMPORT_LINE = "from src.hadocs.reports.html_hook import generate_html_dashboard\n"
CALL_BLOCK = """    generate_html_dashboard(
        out,
        project_name,
        model,
        executive,
        incidents,
        raw_incidents,
        history_comparison,
        now,
    )
"""


def main():
    if not GEN.exists():
        raise SystemExit(f"Cannot find {GEN}")
    text = GEN.read_text(encoding="utf-8")
    if IMPORT_LINE not in text:
        marker = "from src.hadocs.utils.text import slugify, write_md\n"
        text = text.replace(marker, marker + IMPORT_LINE) if marker in text else IMPORT_LINE + text
    if "generate_html_dashboard(" not in text:
        marker = "    history_comparison = compare_last_two(cfg)\n"
        if marker not in text:
            raise SystemExit("Could not find history_comparison line. Patch generator.py manually.")
        text = text.replace(marker, marker + "\n" + CALL_BLOCK, 1)
    GEN.write_text(text, encoding="utf-8")
    print("v0.10.0 HTML dashboard hook applied.")

if __name__ == "__main__":
    main()
