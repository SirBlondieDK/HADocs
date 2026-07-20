# Windows packaging

This directory contains the Windows packaging configuration for HADocs.

## Build the executable

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1
```

Output:

```text
dist/HADocs/HADocs.exe
```

## Build the installer

Install Inno Setup, then compile:

```text
installer/HADocs.iss
```

Run the complete test suite before creating a release artifact. See the [release checklist](../docs/release/Release-Checklist.md).
