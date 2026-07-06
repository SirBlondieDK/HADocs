# v1.0.1 HTML dashboard output fix

Fixes a regression where scan generated:

- `output/index.md`
- `output/explorer/index.html`

but did **not** generate:

- `output/index.html`

## Cause

The compatibility wrapper routed the HTML dashboard call to `generate_index(...)`,
which creates the Markdown index, not the HTML dashboard.

## Fix

`generate_html_dashboard(...)` now routes the current 10-argument dashboard call
to:

```python
generate_executive_dashboard(...)
```

and only routes the old 5-argument legacy call to:

```python
generate_index(...)
```
