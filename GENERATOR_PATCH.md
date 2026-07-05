# v0.10.0 generator patch

After copying the v0.10.0 files into your project, run:

```powershell
py -3.14 tools_apply_v0_10_patch.py
```

This adds the HTML dashboard call to `src/hadocs/reports/generator.py`.

Then run:

```powershell
py -3.14 -m pytest
py -3.14 main.py
```

Open:

```text
output/index.html
```
