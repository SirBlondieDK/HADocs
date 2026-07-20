# v1.0.1 Model object wrapper fix

Fixes:

```text
'dict' object has no attribute 'devices'
```

The HTML dashboard generator expects `model.devices`, `model.entities`, etc.
The compatibility wrapper was passing a plain dictionary.

This patch wraps dict/empty model values in a `SimpleNamespace` with the expected
attributes.
