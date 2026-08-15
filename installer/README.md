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
directory.

Outputs:

```text
dist/windows/staging/HADocs/HADocs.exe
dist/windows/portable/HADocs_v0.17.0-rc4_win64.zip
dist/windows/installer/HADocs_Setup_v0.17.0-rc4.exe
dist/windows/manifests/common-payload.sha256
```

## Build the installer

Install Inno Setup 6 before running the complete script. A local manual-test
installer can be named unambiguously with:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1 -SkipTests -SkipDependencies -TestArtifact
```

For RC4 this produces `HADocs_Setup_v0.17.0-rc4-audit-test.exe`. Test
installers are local validation artifacts and are not published as releases.
To preserve an existing local build, select a distinct ignored output root:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1 -SkipTests -SkipDependencies -TestArtifact -ArtifactRoot dist/windows-rc4-audit
```

The portable payload has no runtime marker. The installer wrapper adds
`installer/installed-runtime.marker` as `.hadocs-installed` beside `HADocs.exe`.
That marker is the explicit contract selecting `%LOCALAPPDATA%\HADocs`; it is
the only intended payload difference. The installer never removes that user
data directory during uninstall.

Run the complete test suite before creating a release artifact. See the [release checklist](../docs/release/Release-Checklist.md).
