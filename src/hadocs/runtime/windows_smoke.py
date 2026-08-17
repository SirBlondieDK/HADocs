from __future__ import annotations

from pathlib import Path

from hadocs.version import __version__


def run_windows_runtime_smoke() -> str:
    """Initialize frozen GUI dependencies without config, credentials, or a window."""

    import _tkinter
    import tkinter

    interpreter = tkinter.Tcl()
    tcl_patchlevel = str(interpreter.eval("info patchlevel"))

    from hadocs.gui.app import run_gui
    import hadocs.security.credential_store  # noqa: F401

    if not callable(run_gui):
        raise RuntimeError("HADocs GUI entry point is unavailable")

    package_root = Path(__file__).resolve().parents[1]
    required_assets = (
        package_root / "web/static/app.js",
        package_root / "web/static/hask-preview.html",
        package_root / "web/static/index.html",
        package_root / "web/static/style.css",
        package_root / "knowledge/hask_bundle/0.2.1/manifest.json",
        package_root / "hudd/data/hudd.sqlite",
    )
    missing = [path for path in required_assets if not path.is_file()]
    if missing:
        raise RuntimeError(
            "required packaged GUI resources are unavailable: "
            + ", ".join(path.name for path in missing)
        )

    return (
        f"hadocs runtime smoke ok: {__version__}; "
        f"Tcl {tcl_patchlevel}; Tk {_tkinter.TK_VERSION}"
    )
