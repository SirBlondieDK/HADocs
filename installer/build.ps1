$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "HADocs Windows Build" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan

if (!(Test-Path "main.py")) {
    Write-Host "ERROR: Run this script from the repository root: C:\HomeAssistantDocs" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "1/5 Running tests..." -ForegroundColor Cyan
py -3.14 -m pytest

Write-Host ""
Write-Host "2/5 Installing build dependencies..." -ForegroundColor Cyan
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pip install pyinstaller

Write-Host ""
Write-Host "3/5 Cleaning old build output..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Host ""
Write-Host "4/5 Building HADocs.exe..." -ForegroundColor Cyan
py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm

if (!(Test-Path "dist\HADocs\HADocs.exe")) {
    Write-Host "ERROR: Build finished but dist\HADocs\HADocs.exe was not created." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "5/5 Build complete." -ForegroundColor Green
Write-Host ""
Write-Host "Executable:" -ForegroundColor Green
Write-Host "dist\HADocs\HADocs.exe"
Write-Host ""
Write-Host "Run it with:" -ForegroundColor Yellow
Write-Host '& ".\dist\HADocs\HADocs.exe"'
