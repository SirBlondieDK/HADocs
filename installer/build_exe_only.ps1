$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "build_windows.ps1") -SkipTests -SkipPackaging -SkipInstaller
