# Windows packaging

This directory contains the Windows packaging configuration for HADocs.

## Canonical Windows build

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1
```

The script builds the program files exactly once in the canonical staging
directory, creates the portable ZIP from that directory, verifies every common
file by relative path and SHA-256, and then points Inno Setup at the same
directory. It installs the versioned toolchain from `requirements-build.txt`
before running tests and invokes pip, pytest, and PyInstaller through one Python
3.14 interpreter. CI passes the interpreter installed by `actions/setup-python`
explicitly; local builds resolve `py -3.14` when no interpreter is supplied.

The two release-packaging workflows pin Python `3.14.3`, the known-good
physical Tcl/Tk 8.6 layout used by the accepted RC5 audit installer. Ordinary
Python test workflows continue to follow the current Python 3.14 patch release.
The pin prevents a release build from silently switching Tcl/Tk layouts; it is
backed by fail-closed validation rather than used as a substitute for it.

Before PyInstaller starts, the canonical script imports tkinter, initializes a
display-free Tcl interpreter, imports the HADocs GUI and credential modules,
and requires physical Tcl and Tk data sources including `init.tcl` and
`tk.tcl`. After staging and again after portable ZIP extraction, it validates
the remapped `_internal\_tcl_data` and `_internal\_tk_data` trees, required
packaged resources and privacy boundaries. It then runs both
`HADocs.exe --version` and the noninteractive GUI/Tcl runtime smoke command.
Any missing runtime data, failed executable, or wrong version stops the build.

Outputs:

```text
dist/windows/staging/HADocs/HADocs.exe
dist/windows/portable/HADocs_v0.17.0-rc5_win64.zip
dist/windows/installer/HADocs_Setup_v0.17.0-rc5.exe
dist/windows/manifests/common-payload.sha256
```

## Build the installer

Install Inno Setup 6 before running the complete script. A local manual-test
installer can be named unambiguously with:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1 -SkipTests -SkipDependencies -TestArtifact
```

Use `-SkipDependencies` only when `requirements-build.txt` has already been
installed into the same Python 3.14 interpreter used for the build. The script
always verifies PyInstaller through that interpreter before staging begins.

For RC5 this produces `HADocs_Setup_v0.17.0-rc5-audit-test.exe`. Test
installers are local validation artifacts and are not published as releases.
To preserve an existing local build, select a distinct ignored output root:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1 -SkipTests -SkipDependencies -TestArtifact -ArtifactRoot dist/windows-rc5-audit
```

The portable payload has no runtime marker. The installer wrapper adds
`installer/installed-runtime.marker` as `.hadocs-installed` beside `HADocs.exe`.
That marker is the explicit contract selecting `%LOCALAPPDATA%\HADocs`; it is
the only intended payload difference. The installer never removes that user
data directory during uninstall.

Run the complete test suite before creating a release artifact. See the [release checklist](../docs/release/Release-Checklist.md).
