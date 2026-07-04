# GitHub setup

## Opret repo

1. Gå til GitHub
2. Opret et nyt repository, fx `homeassistant-docs`
3. Vælg privat eller public

## Fra PowerShell

```powershell
cd C:\HomeAssistantDocs
git init
git add .
git commit -m "Initial project structure"
git branch -M main
git remote add origin https://github.com/DIT-BRUGERNAVN/homeassistant-docs.git
git push -u origin main
```

## Husk

Læg aldrig `config.json` med token på GitHub.
Brug kun `config.example.json`.
