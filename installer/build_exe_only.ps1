$ErrorActionPreference = "Stop"

if (!(Test-Path "main.py")) {
    Write-Host "ERROR: Run this script from the repository root." -ForegroundColor Red
    exit 1
}

py -3.14 -m pip install pyinstaller

if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm

Write-Host "Build complete: dist\HADocs\HADocs.exe" -ForegroundColor Green
