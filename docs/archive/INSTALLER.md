# Installer

## Build executable

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1
```

## Build setup installer

Install Inno Setup and compile:

```text
installer/HADocs.iss
```

The installer remains local-first. It adds no telemetry, cloud upload, analytics, tracking or AI calls.
