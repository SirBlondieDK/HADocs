import os
import sys
import tempfile
import traceback
from collections.abc import Callable
from pathlib import Path


def _ensure_source_package_path() -> None:
    """Prefer the src package when running directly from a repository checkout."""

    if getattr(sys, "frozen", False):
        return

    source_directory = Path(__file__).resolve().parent / "src"
    if source_directory.is_dir():
        source_path = str(source_directory)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)


def main() -> int:
    _ensure_source_package_path()

    if len(sys.argv) > 1:
        from hadocs.cli.main import main as run_cli

        return run_cli()

    _hide_frozen_console()
    return _run_gui()


def _run_gui(gui_runner: Callable[[], None] | None = None) -> int:
    """Run the GUI and report startup failures after the console is hidden."""

    try:
        if gui_runner is None:
            from hadocs.gui.app import run_gui

            gui_runner = run_gui

        gui_runner()
        return 0
    except Exception:
        details = traceback.format_exc()
        log_path = _write_gui_startup_error(details)
        _show_gui_startup_error(log_path)
        return 1


def _write_gui_startup_error(details: str) -> Path | None:
    """Write the latest GUI startup traceback to a user-writable directory."""

    candidate_directories = []

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate_directories.append(Path(local_app_data))

    candidate_directories.append(Path(tempfile.gettempdir()))

    for base_directory in candidate_directories:
        log_path = base_directory / "HADocs" / "logs" / "startup-error.log"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(details, encoding="utf-8")
            return log_path
        except OSError:
            continue

    return None


def _show_gui_startup_error(log_path: Path | None) -> None:
    """Show a visible Windows error after a windowed startup failure."""

    if log_path is None:
        location = "The startup log could not be written."
    else:
        location = f"Details were written to:\n{log_path}"

    message = (
        "HADocs could not start.\n\n"
        f"{location}\n\n"
        "Please include this log when reporting the problem."
    )

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None,
                message,
                "HADocs startup error",
                0x10,
            )
            return
        except (AttributeError, OSError):
            pass

    print(message, file=sys.stderr)


def _hide_frozen_console() -> None:
    """Keep the console bootloader available for CLI output but hide it for GUI use."""

    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return

    try:
        import ctypes

        window = ctypes.windll.kernel32.GetConsoleWindow()
        if window:
            ctypes.windll.user32.ShowWindow(window, 0)
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
