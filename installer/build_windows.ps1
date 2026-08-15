param(
    [switch]$SkipTests,
    [switch]$SkipDependencies,
    [switch]$SkipPackaging,
    [switch]$SkipInstaller,
    [switch]$TestArtifact
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepositoryRoot

if (!(Test-Path -LiteralPath (Join-Path $RepositoryRoot "main.py"))) {
    throw "Run this script from a HADocs repository checkout."
}

$Version = "0.17.0-rc3"
$WindowsRoot = Join-Path $RepositoryRoot "dist\windows"
$StageParent = Join-Path $WindowsRoot "staging"
$Stage = Join-Path $StageParent "HADocs"
$ManifestDirectory = Join-Path $WindowsRoot "manifests"
$PortableDirectory = Join-Path $WindowsRoot "portable"
$InstallerDirectory = Join-Path $WindowsRoot "installer"
$WorkDirectory = Join-Path $RepositoryRoot "build\windows"

function Assert-NativeSuccess([string]$Action) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE."
    }
}

if (!$SkipTests) {
    py -3.14 -m pytest
    Assert-NativeSuccess "Test suite"
}

if (!$SkipDependencies) {
    py -3.14 -m pip install -r requirements.txt
    Assert-NativeSuccess "Runtime dependency installation"
    py -3.14 -m pip install pyinstaller
    Assert-NativeSuccess "PyInstaller installation"
}

if (Test-Path -LiteralPath $WindowsRoot) {
    Remove-Item -LiteralPath $WindowsRoot -Recurse -Force
}
if (Test-Path -LiteralPath $WorkDirectory) {
    Remove-Item -LiteralPath $WorkDirectory -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StageParent, $ManifestDirectory | Out-Null

py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm --distpath $StageParent --workpath $WorkDirectory
Assert-NativeSuccess "Canonical PyInstaller staging build"
if (!(Test-Path -LiteralPath (Join-Path $Stage "HADocs.exe"))) {
    throw "Canonical Windows staging build did not create HADocs.exe."
}
if (Test-Path -LiteralPath (Join-Path $Stage ".hadocs-installed")) {
    throw "Installer marker must never be present in the portable staging payload."
}

function Get-PayloadManifest([string]$Root) {
    $rootPath = (Resolve-Path -LiteralPath $Root).Path
    Get-ChildItem -LiteralPath $rootPath -File -Recurse | Sort-Object FullName | ForEach-Object {
        $relative = $_.FullName.Substring($rootPath.Length).TrimStart('\').Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $relative"
    }
}

$CommonManifest = Join-Path $ManifestDirectory "common-payload.sha256"
Get-PayloadManifest $Stage | Set-Content -LiteralPath $CommonManifest -Encoding utf8

if (!$SkipPackaging) {
    New-Item -ItemType Directory -Force -Path $PortableDirectory | Out-Null
    $PortableZip = Join-Path $PortableDirectory "HADocs_v${Version}_win64.zip"
    Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $PortableZip -Force

    $VerificationRoot = Join-Path $WindowsRoot "portable-verification"
    New-Item -ItemType Directory -Force -Path $VerificationRoot | Out-Null
    Expand-Archive -LiteralPath $PortableZip -DestinationPath $VerificationRoot -Force
    $PortableManifest = Join-Path $ManifestDirectory "portable-payload.sha256"
    Get-PayloadManifest $VerificationRoot | Set-Content -LiteralPath $PortableManifest -Encoding utf8
    if ((Get-Content -Raw $CommonManifest) -cne (Get-Content -Raw $PortableManifest)) {
        throw "Portable ZIP payload differs from canonical staging."
    }
    Remove-Item -LiteralPath $VerificationRoot -Recurse -Force
}

if (!$SkipInstaller) {
    $ProgramFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
    $CompilerCandidates = @(
        (Join-Path $ProgramFilesX86 "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )
    $Compiler = $CompilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (!$Compiler) {
        throw "Inno Setup 6 compiler was not found. Use -SkipInstaller only for an explicit executable-only build."
    }
    New-Item -ItemType Directory -Force -Path $InstallerDirectory | Out-Null
    $OutputName = if ($TestArtifact) { "HADocs_Setup_v${Version}-pathfix-audit-test" } else { "HADocs_Setup_v${Version}" }
    & $Compiler "/DMyPayloadDir=$Stage" "/DMyOutputDir=$InstallerDirectory" "/DMyOutputBaseFilename=$OutputName" "installer\HADocs.iss"
    Assert-NativeSuccess "Inno Setup compilation"
    Copy-Item -LiteralPath $CommonManifest -Destination (Join-Path $ManifestDirectory "installer-common-payload.sha256")
}

Write-Host "Canonical staging: $Stage" -ForegroundColor Green
Write-Host "Common manifest:   $CommonManifest" -ForegroundColor Green
