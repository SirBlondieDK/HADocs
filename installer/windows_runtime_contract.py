from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence


class RuntimeContractError(RuntimeError):
    """Raised when a Windows frozen-runtime requirement is not satisfied."""


TCL_PAYLOAD_DIRECTORY = Path("_internal") / "_tcl_data"
TK_PAYLOAD_DIRECTORY = Path("_internal") / "_tk_data"
REQUIRED_GUI_ASSETS = (
    Path("_internal/hadocs/web/static/app.js"),
    Path("_internal/hadocs/web/static/hask-preview.html"),
    Path("_internal/hadocs/web/static/index.html"),
    Path("_internal/hadocs/web/static/style.css"),
)
ALLOWED_PACKAGED_DATABASE = Path(
    "_internal/hadocs/hudd/data/hudd.sqlite"
)


def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise RuntimeContractError(f"{description} is missing: {path}")


def _require_directory(path: Path, description: str) -> None:
    if not path.is_dir():
        raise RuntimeContractError(f"{description} is missing: {path}")


def validate_source_layout(tcl_data_dir: Path, tk_data_dir: Path) -> None:
    """Validate the physical Tcl/Tk sources PyInstaller is expected to collect."""

    _require_directory(tcl_data_dir, "Tcl library/data directory")
    _require_file(tcl_data_dir / "init.tcl", "Tcl initialization script")
    _require_directory(tk_data_dir, "Tk library/data directory")
    _require_file(tk_data_dir / "tk.tcl", "Tk initialization script")


def inspect_build_interpreter() -> dict[str, str]:
    """Initialize Tcl without a display and return the selected build contract."""

    if sys.version_info[:2] != (3, 14):
        raise RuntimeContractError("Python 3.14 is required for Windows packaging")

    try:
        import _tkinter
        import tkinter
    except ImportError as error:
        raise RuntimeContractError(
            "tkinter cannot be imported by the selected build interpreter"
        ) from error

    try:
        interpreter = tkinter.Tcl()
        patchlevel = str(interpreter.eval("info patchlevel"))
        tcl_data_dir = Path(str(interpreter.eval("info library"))).resolve()
    except tkinter.TclError as error:
        raise RuntimeContractError(
            "the selected build interpreter cannot initialize Tcl"
        ) from error

    tk_version = str(_tkinter.TK_VERSION)
    configured_tk_dir = os.environ.get("TK_LIBRARY", "").strip()
    tk_data_dir = (
        Path(configured_tk_dir).resolve()
        if configured_tk_dir
        else (tcl_data_dir.parent / f"tk{tk_version}").resolve()
    )
    validate_source_layout(tcl_data_dir, tk_data_dir)

    repository_root = Path(__file__).resolve().parents[1]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    try:
        from hadocs.gui.app import run_gui
        import hadocs.security.credential_store  # noqa: F401
    except ImportError as error:
        raise RuntimeContractError(
            "HADocs GUI or credential modules cannot be imported"
        ) from error
    if not callable(run_gui):
        raise RuntimeContractError("HADocs GUI entry point is not callable")

    return {
        "python": sys.version.split()[0],
        "python_executable": str(Path(sys.executable).resolve()),
        "tcl": patchlevel,
        "tk": tk_version,
        "tcl_data_dir": str(tcl_data_dir),
        "tk_data_dir": str(tk_data_dir),
    }


def _validate_no_mutable_payload(root: Path) -> None:
    forbidden_directories = {"config", "output", "cache", "logs", "credentials"}
    forbidden_filenames = {
        "config.json",
        "credentials.json",
        "hadocs.db",
        "hadocs.sqlite",
        "hadocs.sqlite3",
    }

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        lowered_parts = {part.casefold() for part in relative.parts[:-1]}
        lowered_name = relative.name.casefold()
        if lowered_parts & forbidden_directories:
            raise RuntimeContractError(
                f"mutable runtime directory is present in payload: {relative}"
            )
        if lowered_name in forbidden_filenames or lowered_name.endswith(
            (".wal", ".log")
        ):
            raise RuntimeContractError(
                f"mutable runtime file is present in payload: {relative}"
            )
        if relative.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
            if relative != ALLOWED_PACKAGED_DATABASE:
                raise RuntimeContractError(
                    f"operational database is present in payload: {relative}"
                )


def validate_payload(root: Path) -> dict[str, int]:
    """Validate required Tcl/Tk/resources and forbidden mutable payload paths."""

    root = root.resolve()
    _require_directory(root, "Windows payload root")
    _require_file(root / "HADocs.exe", "frozen HADocs executable")
    if (root / ".hadocs-installed").exists():
        raise RuntimeContractError(
            "installed-runtime marker must not be present in canonical payload"
        )

    tcl_data_dir = root / TCL_PAYLOAD_DIRECTORY
    tk_data_dir = root / TK_PAYLOAD_DIRECTORY
    validate_source_layout(tcl_data_dir, tk_data_dir)

    for relative in REQUIRED_GUI_ASSETS:
        _require_file(root / relative, f"required GUI asset {relative.as_posix()}")

    hask_020 = root / "_internal/hadocs/knowledge/hask_bundle/0.2.0"
    if hask_020.exists():
        raise RuntimeContractError("HASK bundle 0.2.0 must not be packaged")
    hask_021 = root / "_internal/hadocs/knowledge/hask_bundle/0.2.1"
    hask_files = tuple(sorted(hask_021.glob("*.json")))
    if len(hask_files) != 14:
        raise RuntimeContractError(
            "HASK bundle 0.2.1 must contain exactly 14 JSON artifacts"
        )

    _validate_no_mutable_payload(root)
    return {
        "files": sum(1 for path in root.rglob("*") if path.is_file()),
        "tcl_files": sum(1 for path in tcl_data_dir.rglob("*") if path.is_file()),
        "tk_files": sum(1 for path in tk_data_dir.rglob("*") if path.is_file()),
        "hask_021_json": len(hask_files),
    }


def smoke_executable(
    executable: Path,
    expected_version: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Run version and noninteractive GUI/Tcl smoke checks on a frozen executable."""

    executable = executable.resolve()
    _require_file(executable, "frozen HADocs executable")

    commands: Sequence[tuple[list[str], str, str]] = (
        (
            [str(executable), "--version"],
            f"hadocs {expected_version}",
            "version smoke-test",
        ),
        (
            [str(executable), "--windows-runtime-smoke"],
            f"hadocs runtime smoke ok: {expected_version}; Tcl ",
            "GUI/Tcl runtime smoke-test",
        ),
    )
    for command, expected_output, description in commands:
        try:
            result = runner(
                command,
                cwd=executable.parent,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeContractError(f"{description} could not run") from error
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "no output").strip()
            raise RuntimeContractError(
                f"{description} failed with exit code {result.returncode}: {details}"
            )
        output = result.stdout.strip()
        if description == "version smoke-test" and output != expected_output:
            raise RuntimeContractError(
                f"{description} returned {output!r}; expected {expected_output!r}"
            )
        if description != "version smoke-test" and not output.startswith(
            expected_output
        ):
            raise RuntimeContractError(
                f"{description} returned unexpected output: {output!r}"
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate HADocs Windows runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect-interpreter")
    payload = subparsers.add_parser("validate-payload")
    payload.add_argument("--root", type=Path, required=True)
    smoke = subparsers.add_parser("smoke-executable")
    smoke.add_argument("--executable", type=Path, required=True)
    smoke.add_argument("--expected-version", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "inspect-interpreter":
            print(json.dumps(inspect_build_interpreter(), sort_keys=True))
        elif args.command == "validate-payload":
            print(json.dumps(validate_payload(args.root), sort_keys=True))
        else:
            smoke_executable(args.executable, args.expected_version)
            print(f"frozen runtime smoke passed: {args.executable}")
    except RuntimeContractError as error:
        print(f"Windows runtime contract failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
