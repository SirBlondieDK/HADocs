# Windows

The Windows release provides a self-contained HADocs installation and does not require a separate Python runtime.

## Install

1. Download the latest Windows release from [GitHub Releases](https://github.com/SirBlondieDK/HADocs/releases).
2. Extract the ZIP archive.
3. Run `HADocs.exe`.
4. Enter the Home Assistant URL and Long-Lived Access Token.
5. Start the HADocs web interface or run an analysis.
6. Open the local address shown by HADocs.

The Home Assistant token is stored in Windows Credential Manager and is not written to `config.json`.

## Run from source

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
$env:HADOCS_OUTPUT_DIR = Join-Path (Get-Location) "output"
py -3.14 -m src.hadocs.web.app
```

## HASK Preview

HASK Preview is experimental and disabled by default. In Settings, enable both
**HASK Preview** and **HASK**. Leave the operational database, candidate bridge,
and native-status controls disabled unless those independent features are also
intended. Without an explicit bundle path, the installed Windows package uses
its validated read-only packaged bundle. Set both flags back to false to disable
Preview. Candidate output never affects normal findings, Root Causes,
recommendations, or Health Score.

For build instructions, see the [Windows packaging guide](../../../installer/README.md). For general navigation, return to the [documentation home](../../README.md).
