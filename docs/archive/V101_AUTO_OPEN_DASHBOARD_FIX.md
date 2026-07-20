# v1.0.1 Auto-open dashboard fix

Fixes **Open dashboard after scan** after the Credential Manager config changes.

The scan worker was checking `self.cfg` instead of the runtime `cfg` returned by `get_cfg()`.

It now uses:

```python
if cfg.get("open_dashboard_after_scan", True):
    self.after(250, lambda: open_dashboard(cfg.get("output_dir", "output")))
```

Using `self.after(...)` also makes opening the browser safer from the worker thread.
