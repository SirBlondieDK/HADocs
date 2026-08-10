from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_gui_module_imports_in_fresh_process_without_circular_import():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from hadocs.gui.app import run_gui; assert callable(run_gui)",
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_repository_main_uses_src_package_without_pythonpath():
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, "main.py", "--version"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("hadocs ")

def test_gui_startup_failure_is_logged_and_returns_nonzero(tmp_path, monkeypatch):
    import main as launcher

    displayed_paths = []
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(
        launcher,
        "_show_gui_startup_error",
        displayed_paths.append,
    )

    def failing_gui():
        raise RuntimeError("simulated GUI startup failure")

    result = launcher._run_gui(failing_gui)

    expected_log = tmp_path / "HADocs" / "logs" / "startup-error.log"
    assert result == 1
    assert expected_log.is_file()
    assert "RuntimeError: simulated GUI startup failure" in expected_log.read_text(
        encoding="utf-8"
    )
    assert displayed_paths == [expected_log]
