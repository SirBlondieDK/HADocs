# Final import fix

This fixes the circular import by making `html_hook.py` lazy.

`html_hook.py` must not contain this at top level:

```python
from src.hadocs.reports.generator import generate_index
```

It must import inside the function instead.
