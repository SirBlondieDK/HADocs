# v1.0.1 Final dashboard wrapper fix

Fixes:

```text
list indices must be integers or slices, not str
```

The 8-argument dashboard call was being mapped as if it contained a full model
argument. It does not. The wrapper now treats the 8-argument call as:

```python
out, project_name, executive, health_notes,
history_comparison, trend_summary, incidents, now
```

and supplies a safe empty model to the HTML dashboard generator.
