# Architecture

```text
Home Assistant API
        │
        ▼
Collectors
        │
        ▼
Normalized Model
        │
        ├── Rules Engine
        ├── Classification Engine
        ├── Health Engine
        ├── Incident Engine
        ├── Incident Collapse Engine
        ├── Relationship Engine
        ├── Recommendation Engine
        ├── Knowledge Engine
        └── Privacy Engine
        │
        ▼
Renderers
        ├── HTML
        ├── Markdown
        ├── CSV
        └── JSON
```

Analysis logic should live in engines, not renderers.
