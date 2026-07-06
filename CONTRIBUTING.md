# Contributing to HADocs

Thank you for considering contributing to HADocs.

## Good contributions

- report bugs
- test on different Home Assistant installations
- improve Root Cause rules
- improve Health Score weighting
- improve screenshots
- improve documentation
- suggest better wording
- add tests
- review generated reports for false positives

## Development setup

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
py -3.14 -m pytest
py -3.14 main.py
```

## Pull requests

Before opening a pull request:

```powershell
py -3.14 -m pytest
```

Please keep PRs focused.

## Privacy

Do not include real Home Assistant tokens, private URLs, personal device names or private generated reports in issues or pull requests unless redacted.
