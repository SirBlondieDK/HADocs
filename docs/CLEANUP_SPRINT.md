# HADocs Cleanup Sprint

Apply this before starting Automation Toolbox.

## What it does

- Updates `.gitignore`.
- Moves temporary patch scripts from `tools/` to `archive/dev-tools/`.
- Adds `docs/cleanup.md`.
- Keeps local `build/`, `dist/` and `output/` files on disk, but prevents future accidental commits.

## Apply

```powershell
py -3.14 tools/cleanup_project.py
py -3.14 -m pytest
git status
```

If Git still tracks build artifacts:

```powershell
git rm -r --cached build dist output
```

Then commit:

```powershell
git add .gitignore docs/cleanup.md archive/dev-tools tools
git commit -m "Clean up project structure"
git push
```
