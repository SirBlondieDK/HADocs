$ErrorActionPreference = "Stop"

Write-Host "Building HADocs Windows executable..." -ForegroundColor Cyan

if (!(Test-Path "main.py")) {
    Write-Host "Run this script from the repository root." -ForegroundColor Red
    exit 1
}

py -3.14 -m pip install --upgrade pip
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pip install pyinstaller

if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm

Write-Host ""
Write-Host "Build complete:" -ForegroundColor Green
Write-Host "dist\HADocs\HADocs.exe"
