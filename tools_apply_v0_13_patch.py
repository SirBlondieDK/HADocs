from pathlib import Path


GEN = Path("src/hadocs/reports/generator.py")
IMPORT_LINE = "from src.hadocs.html.explorer import write_explorer\n"


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

    if "write_explorer(out, model, graph)" not in text:
        marker = "    history_comparison = compare_last_two(cfg)\n"
        call = "\n    write_explorer(out, model, graph)\n"
        if marker in text:
            text = text.replace(marker, marker + call, 1)
        else:
            marker2 = "    generate_index("
            if marker2 in text:
                text = text.replace(marker2, "    write_explorer(out, model, graph)\n\n" + marker2, 1)
            else:
                print("Could not auto-patch write_explorer call. Add it manually.")

    GEN.write_text(text, encoding="utf-8")
    print("v0.13.0 Explorer Foundation hook applied.")


if __name__ == "__main__":
    main()
