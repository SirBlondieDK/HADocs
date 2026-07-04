# GitHub setup

## Initial push

```powershell
cd C:\HomeAssistantDocs
git init
git add .
git commit -m "Initial HADocs project"
git branch -M main
git remote add origin https://github.com/SirBlondieDK/HADocs.git
git push -u origin main
```

## Important

Never commit `config.json`, `cache/`, or `output/`.
