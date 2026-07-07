# Issue #4 Step 3: Area filename helper

Extends `src/hadocs/utils/display.py` with `area_filename()`.

Unassigned Home Assistant areas can now generate:

```text
no_area.md
```

Normal areas still use the existing `slugify()` behavior.

No generator behavior is changed in this step.
