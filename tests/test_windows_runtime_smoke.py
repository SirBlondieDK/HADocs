from __future__ import annotations

import sys

import main as launcher
import pytest

from hadocs.runtime.windows_smoke import run_windows_runtime_smoke


def test_noninteractive_windows_runtime_smoke_initializes_gui_contract() -> None:
    result = run_windows_runtime_smoke()

    assert result.startswith("hadocs runtime smoke ok: 0.17.0-rc5; Tcl ")
    assert "; Tk " in result


def test_launcher_runtime_smoke_does_not_bootstrap_user_data(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(sys, "argv", ["HADocs.exe", "--windows-runtime-smoke"])
    monkeypatch.setattr(
        launcher,
        "_bootstrap_runtime",
        lambda: pytest.fail("runtime smoke must not bootstrap user data"),
    )

    assert launcher.main() == 0
    assert "hadocs runtime smoke ok: 0.17.0-rc5" in capsys.readouterr().out
