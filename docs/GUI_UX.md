# GUI UX

v0.14 improves what happens after a scan completes.

## Goal

A new user should not have to search for generated files.

After a successful scan, HADocs should make it obvious what to open next.

## Recommended output actions

- Open Dashboard: `output/index.html`
- Open Explorer: `output/explorer/index.html`
- Open Markdown: `output/index.md`
- Open Output Folder: `output/`

## Completion message

Recommended wording:

```text
Documentation successfully generated.

Dashboard: output/index.html
Explorer: output/explorer/index.html
Knowledge Pack: output/knowledge/
Markdown: output/index.md
```

## Future GUI goals

- Health Score in GUI
- Main root cause in GUI
- Potential score in GUI
- One-click open dashboard after scan
- Optional auto-open dashboard checkbox
