# v0.14 Explain This direct fix

This patch uses the current `render_root_cards()` structure and inserts a visible
`Explain this` panel directly after the root-cause reason text.

## Apply

```powershell
py -3.14 tools/apply_v014_explain_this_direct_fix.py
py -3.14 -m pytest
py -3.14 main.py
```

Then open `output/index.html` and expand `Explain this` on a Root Cause card.
