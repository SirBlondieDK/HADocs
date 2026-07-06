# v0.14 Explain This fix

Adds visible **Explain this** sections to Root Cause cards in `output/index.html`.

## Apply

```powershell
py -3.14 tools/apply_v014_explain_this_fix.py
py -3.14 -m pytest
py -3.14 main.py
```

Then open `output/index.html` and expand a Root Cause card.
