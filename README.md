# Home Assistant Docs

Dokumentations- og analyseværktøj til Home Assistant.

## Funktioner

- Henter data via Home Assistant REST + WebSocket API
- Genererer dokumentation pr. rum
- Genererer dokumentation pr. enhed
- Finder unknown/unavailable entities
- Finder enheder og entiteter uden rum
- Finder dubletter i friendly names
- Laver serverrum-rapport
- Laver netværksrapport
- Laver batterirapport
- Laver dashboard whitelist
- Laver CSV-export
- Beregner Health Score

## Installation

```powershell
cd C:\HomeAssistantDocs
pip install -r requirements.txt
```

## GUI

```powershell
python main.py
```

## CLI

```powershell
copy config.example.json config.json
notepad config.json
python -m src.hadocs.cli
```

## Output

Start med:

```text
output\index.md
```
