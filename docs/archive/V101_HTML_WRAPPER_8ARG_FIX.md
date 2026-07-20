# v1.0.1 HTML wrapper 8-argument fix

Fixes:

```text
generate_html_dashboard expected either 5 legacy args or 10+ dashboard args, got 8
```

The wrapper now supports:

- 5 args: legacy markdown index
- 8 args: dashboard call without incident lists
- 9 args: dashboard call with incidents
- 10+ args: full dashboard call
