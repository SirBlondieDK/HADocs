from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from installer.windows_runtime_contract import (
    RuntimeContractError,
    smoke_executable,
    validate_payload,
    validate_source_layout,
)


def make_source_layout(root: Path) -> tuple[Path, Path]:
    tcl = root / "tcl9.0"
    tk = root / "tk9.0"
    tcl.mkdir(parents=True)
    tk.mkdir(parents=True)
    (tcl / "init.tcl").write_text("# synthetic Tcl init", encoding="utf-8")
    (tk / "tk.tcl").write_text("# synthetic Tk init", encoding="utf-8")
    return tcl, tk


def make_payload(root: Path) -> Path:
    payload = root / "HADocs"
    (payload / "HADocs.exe").parent.mkdir(parents=True)
    (payload / "HADocs.exe").write_bytes(b"synthetic executable")
    tcl = payload / "_internal/_tcl_data"
    tk = payload / "_internal/_tk_data"
    tcl.mkdir(parents=True)
    tk.mkdir(parents=True)
    (tcl / "init.tcl").write_text("# synthetic Tcl init", encoding="utf-8")
    (tk / "tk.tcl").write_text("# synthetic Tk init", encoding="utf-8")
    for name in ("app.js", "hask-preview.html", "index.html", "style.css"):
        asset = payload / "_internal/hadocs/web/static" / name
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text("synthetic", encoding="utf-8")
    bundle = payload / "_internal/hadocs/knowledge/hask_bundle/0.2.1"
    bundle.mkdir(parents=True)
    for index in range(14):
        (bundle / f"artifact-{index:02}.json").write_text("{}", encoding="utf-8")
    hudd = payload / "_internal/hadocs/hudd/data/hudd.sqlite"
    hudd.parent.mkdir(parents=True)
    hudd.write_bytes(b"read-only synthetic HUDD")
    return payload


def test_source_layout_requires_physical_tcl_and_tk_data(tmp_path: Path) -> None:
    tcl, tk = make_source_layout(tmp_path)
    validate_source_layout(tcl, tk)

    (tcl / "init.tcl").unlink()
    with pytest.raises(RuntimeContractError, match="Tcl initialization script"):
        validate_source_layout(tcl, tk)


@pytest.mark.parametrize(
    ("relative", "message"),
    [
        ("_internal/_tcl_data", "Tcl library/data directory"),
        ("_internal/_tk_data", "Tk library/data directory"),
        ("_internal/_tcl_data/init.tcl", "Tcl initialization script"),
        ("_internal/_tk_data/tk.tcl", "Tk initialization script"),
    ],
)
def test_payload_rejects_missing_tcl_tk_runtime(
    tmp_path: Path, relative: str, message: str
) -> None:
    payload = make_payload(tmp_path)
    target = payload / relative
    if target.is_dir():
        for child in target.iterdir():
            child.unlink()
        target.rmdir()
    else:
        target.unlink()

    with pytest.raises(RuntimeContractError, match=message):
        validate_payload(payload)


def test_payload_accepts_required_resources_and_rejects_mutable_data(
    tmp_path: Path,
) -> None:
    payload = make_payload(tmp_path)
    result = validate_payload(payload)
    assert result["hask_021_json"] == 14

    mutable = payload / "config/config.json"
    mutable.parent.mkdir()
    mutable.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeContractError, match="mutable runtime directory"):
        validate_payload(payload)


def completed(returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def test_frozen_executable_nonzero_exit_fails_closed(tmp_path: Path) -> None:
    executable = tmp_path / "HADocs.exe"
    executable.touch()

    with pytest.raises(RuntimeContractError, match="exit code 1"):
        smoke_executable(
            executable,
            "0.17.0-rc5",
            runner=lambda *args, **kwargs: completed(1, stderr="runtime failed"),
        )


def test_frozen_executable_wrong_version_fails_closed(tmp_path: Path) -> None:
    executable = tmp_path / "HADocs.exe"
    executable.touch()

    with pytest.raises(RuntimeContractError, match="expected 'hadocs 0.17.0-rc5'"):
        smoke_executable(
            executable,
            "0.17.0-rc5",
            runner=lambda *args, **kwargs: completed(0, stdout="hadocs 0.17.0-rc4\n"),
        )


def test_frozen_executable_runs_version_and_gui_tcl_smokes(tmp_path: Path) -> None:
    executable = tmp_path / "HADocs.exe"
    executable.touch()
    results = iter(
        (
            completed(0, stdout="hadocs 0.17.0-rc5\n"),
            completed(
                0,
                stdout=(
                    "hadocs runtime smoke ok: 0.17.0-rc5; "
                    "Tcl 8.6.15; Tk 8.6\n"
                ),
            ),
        )
    )
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return next(results)

    smoke_executable(executable, "0.17.0-rc5", runner=runner)

    assert [command[1] for command in commands] == [
        "--version",
        "--windows-runtime-smoke",
    ]
