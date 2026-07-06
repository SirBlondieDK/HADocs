
from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")
HOOK = Path("src/hadocs/reports/html_hook.py")
GITIGNORE = Path(".gitignore")


HOOK_TEXT = Backward compatibility wrapper for the HTML dashboard generator.

Do not import ``generator`` at module load time. ``generator.py`` historically
imports this module, so importing ``generator`` here immediately creates a
circular import.

The lazy import inside the function keeps old import paths working without
breaking application startup, tests or PyInstaller builds.
