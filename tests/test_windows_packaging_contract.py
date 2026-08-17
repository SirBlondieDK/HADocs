from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inno_uses_canonical_stage_and_explicit_wrapper_marker() -> None:
    script = (ROOT / "installer/HADocs.iss").read_text(encoding="utf-8")

    assert '#define MyAppVersion "0.17.0-rc5"' in script
    assert '#define MyPayloadDir "..\\dist\\windows\\staging\\HADocs"' in script
    assert 'Source: "{#MyPayloadDir}\\*"' in script
    assert script.count('Source: "{#MyPayloadDir}') == 1
    assert 'Source: "installed-runtime.marker"' in script
    assert 'DestName: ".hadocs-installed"' in script
    assert 'WorkingDir: "{localappdata}\\HADocs"' in script
    assert script.count('WorkingDir: "{localappdata}\\HADocs"') == 3
    assert 'Name: "{localappdata}\\HADocs"' in script
    assert "UninstallDelete" not in script
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in script
    assert "UsedUserAreasWarning=no" in script


def test_portable_and_installer_share_one_build_and_manifest_contract() -> None:
    build = (ROOT / "installer/build_windows.ps1").read_text(encoding="utf-8")

    assert build.count("-m PyInstaller") == 2
    assert build.count("-m PyInstaller installer/HADocs.spec") == 1
    assert "& $Python -m PyInstaller" in build
    assert "py -3.14 -m PyInstaller" not in build
    assert 'Compress-Archive -Path (Join-Path $Stage "*")' in build
    assert "Get-PayloadManifest $Stage" in build
    assert "Get-PayloadManifest $VerificationRoot" in build
    assert "Portable ZIP payload differs from canonical staging" in build
    assert 'Join-Path $Stage ".hadocs-installed"' in build
    assert '"/DMyPayloadDir=$Stage"' in build
    assert "installer-common-payload.sha256" in build
    assert "Assert-NativeSuccess \"Test suite\"" in build
    assert "Assert-NativeSuccess \"Canonical PyInstaller staging build\"" in build
    assert "Assert-NativeSuccess \"Inno Setup compilation\"" in build
    assert "-audit-test" in build
    assert "[string]$ArtifactRoot" in build
    assert "ArtifactRoot must stay inside the repository checkout" in build
    assert 'Join-Path $WindowsRoot "pyinstaller-work"' in build
    assert "inspect-interpreter" in build
    assert build.index("if (!$SkipDependencies)") < build.index(
        "inspect-interpreter"
    )
    assert build.index("inspect-interpreter") < build.index(
        "-m PyInstaller installer/HADocs.spec"
    )
    assert "validate-payload --root $Stage" in build
    assert "validate-payload --root $VerificationRoot" in build
    assert "smoke-executable --executable (Join-Path $Stage" in build
    assert "smoke-executable --executable (Join-Path $VerificationRoot" in build
    assert "Canonical staging executable smoke-test" in build
    assert "Extracted portable executable smoke-test" in build


def test_spec_fails_closed_when_pyinstaller_lacks_tcl_tk_data() -> None:
    spec = (ROOT / "installer/HADocs.spec").read_text(encoding="utf-8")

    assert "tcltk_info.data_files" in spec
    assert "tcltk_info.TCL_ROOTNAME" in spec
    assert "tcltk_info.TK_ROOTNAME" in spec
    assert 'Path(tcltk_info.TCL_ROOTNAME) / "init.tcl"' in spec
    assert 'Path(tcltk_info.TK_ROOTNAME) / "tk.tcl"' in spec
    assert "missing_tcl_tk_destinations" in spec


def test_canonical_build_owns_and_verifies_its_python_toolchain() -> None:
    build = (ROOT / "installer/build_windows.ps1").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements-build.txt").read_text(encoding="utf-8")

    assert "-r requirements.txt" in requirements.splitlines()
    assert re.search(r"^PyInstaller==\d+\.\d+\.\d+$", requirements, re.MULTILINE)
    assert "[string]$PythonExecutable" in build
    assert "& $Python -m pip install -r requirements-build.txt" in build
    assert "& $Python -m PyInstaller --version" in build
    assert "PyInstaller availability for selected Python" in build
    assert build.index("if (!$SkipDependencies)") < build.index(
        "& $Python -m PyInstaller --version"
    )
    assert build.index("& $Python -m PyInstaller --version") < build.index(
        "Remove-Item -LiteralPath $WindowsRoot"
    )
    assert "& $Python -m pytest" in build


def test_ci_uses_the_canonical_windows_build_script() -> None:
    for name in ("build-release.yml", "build-windows.yml"):
        workflow = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
        assert "installer/build_windows.ps1" in workflow
        assert "dist/windows/manifests/*.sha256" in workflow
        assert "permissions:\n  contents: read" in workflow


def test_installer_marker_is_not_in_program_staging_sources() -> None:
    marker = ROOT / "installer/installed-runtime.marker"
    assert marker.read_text(encoding="utf-8").strip() == "HADOCS_INSTALLED_RUNTIME_V1"
    spec = (ROOT / "installer/HADocs.spec").read_text(encoding="utf-8")
    assert "installed-runtime.marker" not in spec


def test_hask_021_still_contains_exactly_fourteen_artifacts() -> None:
    bundle = ROOT / "src/hadocs/knowledge/hask_bundle/0.2.1"
    assert len(tuple(bundle.glob("*.json"))) == 14
