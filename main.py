import sys


def main() -> int:
    if len(sys.argv) > 1:
        from hadocs.cli.main import main as run_cli

        return run_cli()

    _hide_frozen_console()
    from hadocs.gui.app import run_gui

    run_gui()
    return 0


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
