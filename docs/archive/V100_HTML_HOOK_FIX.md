# v1.0.0 html_hook compatibility fix

Adds `src/hadocs/reports/html_hook.py` as a compatibility layer.

This fixes imports like:

```python
from src.hadocs.reports.html_hook import generate_html_dashboard
```

The real implementation is still in:

```python
src.hadocs.reports.html_dashboard
```
