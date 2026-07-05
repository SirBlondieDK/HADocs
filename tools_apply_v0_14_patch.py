from pathlib import Path


APP = Path("src/hadocs/gui/app.py")


IMPORT_BLOCK = """from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)
"""


def main():
    if not APP.exists():
        print("GUI app.py not found. Output helpers were installed; see docs/V0_14_GUI_PATCH.md for manual integration.")
        return

    text = APP.read_text(encoding="utf-8")

    if "from src.hadocs.gui.output_actions import" not in text:
        text = IMPORT_BLOCK + "\n" + text

    # This script intentionally avoids aggressive GUI rewriting because app.py
    # may differ between installations. The helper functions are installed and
    # manual integration notes are in docs/V0_14_GUI_PATCH.md.
    APP.write_text(text, encoding="utf-8")
    print("v0.14.0 GUI output helpers installed.")
    print("See docs/V0_14_GUI_PATCH.md to add buttons if they were not inserted automatically.")


if __name__ == "__main__":
    main()
