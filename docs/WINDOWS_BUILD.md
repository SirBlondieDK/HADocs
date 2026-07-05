# Windows build

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File installer/build.ps1
```

This runs:

1. tests
2. dependency install
3. clean
4. PyInstaller build
5. output verification

The executable is created here:

```text
dist/HADocs/HADocs.exe
```

Run it from PowerShell with:

```powershell
& ".\dist\HADocs\HADocs.exe"
```

Do not run it as:

```powershell
dist\HADocs\HADocs.exe
```

PowerShell needs `.\` or `&`.
