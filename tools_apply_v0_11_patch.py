from pathlib import Path

GEN = Path("src/hadocs/reports/generator.py")
IMPORT_LINE = "from src.hadocs.knowledge.exporter import export_knowledge\n"
CALL = """    export_knowledge(
        out,
        model=model,
        executive=executive,
        incidents=incidents,
        version="0.11.0",
    )
"""


def main():
    if not GEN.exists():
        print("generator.py not found; docs and modules were still installed.")
        return
    text = GEN.read_text(encoding="utf-8")
    if IMPORT_LINE not in text:
        marker = "from src.hadocs.utils.text import slugify, write_md\n"
        text = text.replace(marker, marker + IMPORT_LINE) if marker in text else IMPORT_LINE + text
    if "export_knowledge(" not in text:
        marker = "    history_comparison = compare_last_two(cfg)\n"
        if marker in text:
            text = text.replace(marker, marker + "\n" + CALL, 1)
        else:
            print("Could not auto-patch generator.py. Add export_knowledge call manually.")
    GEN.write_text(text, encoding="utf-8")
    print("v0.11.0 knowledge export hook applied.")


if __name__ == "__main__":
    main()
