# Cleanup guide

If generated files were committed by mistake:

```bash
git rm --cached output.zip
git rm -r --cached output
git commit -m "Remove generated output files"
git push
```

Make sure `.gitignore` contains:

```gitignore
output/
cache/
*.zip
config.json
.env
```
