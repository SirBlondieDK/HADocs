# Windows

The Windows release provides a self-contained HADocs installation and does not require a separate Python runtime.

## Installed and portable modes

An installed copy stores mutable data under `%LOCALAPPDATA%\HADocs`, independent
of its current working directory:

```text
%LOCALAPPDATA%\HADocs\config
%LOCALAPPDATA%\HADocs\output
%LOCALAPPDATA%\HADocs\cache
%LOCALAPPDATA%\HADocs\logs
```

The installer adds a `.hadocs-installed` marker beside the executable. A
portable ZIP does not contain that marker and keeps mutable data beside
`HADocs.exe`. `HADOCS_ROOT` is the documented explicit override and has higher
precedence than either frozen mode. Source checkouts retain their repository
working-directory behavior. Home Assistant App and container deployments keep
their existing explicit `/data`, `/config`, `/output`, and `/cache` contracts.

Packaged resources (HASK bundle, HUDD, schemas, SQL migrations, templates and
static files) remain read-only under the application payload; relative mutable
paths, including a relative `HADOCS_CONFIG_FILE`, are resolved against the
selected data root. Relative resource paths are resolved against the application
payload. Relative paths containing parent traversal cannot escape their selected
root. Explicit absolute paths, including UNC paths, remain supported for users
who deliberately place configuration, output, cache, or database files elsewhere.

On first installed start, valid legacy V0.16/RC2/RC3 configuration and Device
Overrides are copied atomically from the installation directory only when the
destination does not exist. Legacy files are never moved, deleted, or
overwritten. Malformed JSON is ignored. An operational SQLite database already
under `%LOCALAPPDATA%\HADocs` is used in place and is never overwritten. A
database left under the old installation directory is not copied automatically
because SQLite WAL state and protected database identity cannot be migrated
safely by guessing; select or migrate that database explicitly after taking a
consistent backup.

## Install

1. Download the latest Windows release from [GitHub Releases](https://github.com/SirBlondieDK/HADocs/releases).
2. Run the installer, or extract the portable ZIP.
3. Start `HADocs.exe`.
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
