# Testing

Run tests with:

```powershell
py -3.14 -m pytest
```

## Local pytest temp folder

HADocs configures pytest to use:

```text
.pytest_tmp/
```

This avoids Windows permission errors from locked temp folders such as:

```text
C:\Users\<user>\AppData\Local\Temp\pytest-of-<user>
```

## Cleanup

To remove local generated test/cache files:

```powershell
py -3.14 tools_cleanup.py
```

This removes only known generated folders:

- `.pytest_tmp/`
- `.pytest_cache/`
- `__pycache__/`
- `.mypy_cache/`
- `.ruff_cache/`

It does not remove `output/`, `config.json`, or source files.
