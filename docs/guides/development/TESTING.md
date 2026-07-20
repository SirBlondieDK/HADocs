# Testing

Run the complete test suite from the repository root:

```powershell
Remove-Item Env:HADOCS_OUTPUT_DIR -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

Python 3.11 is the minimum supported version; Python 3.14 is used by the current local development workflow. Add or update tests when behavior changes, and verify platform-specific workflows when relevant.

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for the complete development workflow, or return to the [documentation home](../../README.md).
