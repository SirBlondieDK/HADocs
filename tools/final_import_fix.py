from pathlib import Path

HOOK = Path("src/hadocs/reports/html_hook.py")
GEN = Path("src/hadocs/reports/generator.py")

HOOK_TEXT = Backward compatibility wrapper for older HADocs imports.

Important:
This module is imported by generator.py, so it must NOT import generator.py
at module load time. The import is intentionally inside the function to avoid
a circular import during GUI, test and PyInstaller startup.
