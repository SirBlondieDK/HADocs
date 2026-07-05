# HADocs Windows Installer

## Build executable

```powershell
powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1
```

Output:

```text
dist/HADocs/HADocs.exe
```

## Build installer

Install Inno Setup, then compile:

```text
installer/HADocs.iss
```
