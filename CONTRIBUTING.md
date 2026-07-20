# Contributing to HADocs

Thank you for helping improve HADocs. Contributions to code, analysis rules, tests, documentation, and platform support are welcome.

## Before you start

- Search existing issues before opening a new one.
- Keep bug reports free of tokens, private URLs, device names, and unredacted reports.
- Discuss substantial changes in an issue before investing in an implementation.

## Development setup

HADocs requires Python 3.11 or newer. Python 3.14 is used by the current local development workflow.

```powershell
git clone https://github.com/SirBlondieDK/HADocs.git
cd HADocs
py -3.14 -m pip install -e .
$env:HADOCS_OUTPUT_DIR = Join-Path (Get-Location) "output"
py -3.14 -m src.hadocs.web.app
```

## Testing

Run the complete test suite before submitting a change:

```powershell
Remove-Item Env:HADOCS_OUTPUT_DIR -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

Add or update tests when behavior changes. For platform-specific work, also verify the affected Windows, Docker, or Home Assistant workflow.

## Coding style

- Follow the existing project structure and naming conventions.
- Keep the analysis engine deterministic, evidence-based, and independent of presentation code.
- Keep platform entry points thin and preserve behavior across supported platforms.
- Format Python consistently with the project's 100-character line length.
- Update documentation when commands, configuration, output, or user-facing behavior changes.

## Commits and pull requests

- Keep commits focused and use clear, imperative summaries.
- Keep pull requests small enough to review and explain the problem, approach, and verification performed.
- Avoid unrelated refactoring in the same pull request.
- Do not commit generated output, caches, credentials, private Home Assistant data, or local Device Overrides.
- Confirm that all relevant checks pass before requesting review.

## Reporting security issues

Do not report vulnerabilities in a public issue. Follow the responsible disclosure process in [SECURITY.md](SECURITY.md).
