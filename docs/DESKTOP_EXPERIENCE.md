# Desktop Experience

This document describes the new HADocs desktop experience foundation.

## Goals

HADocs should feel like a real desktop application:

- first-run wizard
- settings dialog
- toolbar
- status panel
- progress messages
- output buttons
- about dialog

## New module

```text
src/hadocs/gui/desktop_app.py
```

## Manual integration

To use the new desktop shell, wire your existing generator callback into:

```python
from src.hadocs.gui.desktop_app import run_desktop_gui

run_desktop_gui(run_generate_callback=your_generate_function)
```

The callback receives:

```python
home_assistant_url: str
token: str
project_name: str
```

## Important

This module does not change the analysis engine.

It is a desktop shell around the existing HADocs workflow.
