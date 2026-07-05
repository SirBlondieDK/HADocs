from pathlib import Path


APP = Path("src/hadocs/gui/app.py")

IMPORT_LINE = "from src.hadocs.gui.output_actions import completion_message, open_dashboard, open_explorer, open_markdown, open_output_folder\n"


def main():
    if not APP.exists():
        print("src/hadocs/gui/app.py not found.")
        print("Modern GUI foundation was installed in src/hadocs/gui/modern_app.py")
        return

    text = APP.read_text(encoding="utf-8")

    if "from src.hadocs.gui.output_actions import" not in text:
        text = IMPORT_LINE + text
        APP.write_text(text, encoding="utf-8")

    print("v0.15.0 README and GUI foundation installed.")
    print("Modern GUI foundation: src/hadocs/gui/modern_app.py")
    print("Manual GUI integration notes: docs/GUI_DESKTOP.md")


if __name__ == "__main__":
    main()
