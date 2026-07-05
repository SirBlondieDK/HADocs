from pathlib import Path


GEN = Path("src/hadocs/reports/generator.py")
IMPORT_LINE = "from src.hadocs.knowledge.exporter import export_knowledge\n"


def main():
    if not GEN.exists():
        print("generator.py not found; modules and docs were still installed.")
        return

    text = GEN.read_text(encoding="utf-8")

    if IMPORT_LINE not in text:
        marker = "from src.hadocs.utils.text import slugify, write_md\n"
        if marker in text:
            text = text.replace(marker, marker + IMPORT_LINE)
        else:
            text = IMPORT_LINE + text

    if 'version="0.12.0"' not in text:
        marker = "    history_comparison = compare_last_two(cfg)\n"
        call = (
            "\n"
            "    export_knowledge(\n"
            "        out,\n"
            "        model=model,\n"
            "        executive=executive,\n"
            "        incidents=incidents,\n"
            "        graph=graph,\n"
            "        version=\"0.12.0\",\n"
            "    )\n"
        )
        if marker in text:
            text = text.replace(marker, marker + call, 1)
        else:
            print("Could not auto-patch export_knowledge call. Add it manually.")

    GEN.write_text(text, encoding="utf-8")
    print("v0.12.0 Knowledge Engine hook applied.")


if __name__ == "__main__":
    main()
