# v0.14 GUI patch instructions

This release adds reusable GUI output actions in:

```text
src/hadocs/gui/output_actions.py
```

## Recommended integration in `src/hadocs/gui/app.py`

Add this import:

```python
from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)
```

Add buttons near the existing `Open output` button:

```python
ttk.Button(button_frame, text="Open dashboard", command=lambda: open_dashboard("output")).pack(side="left", padx=4)
ttk.Button(button_frame, text="Open explorer", command=lambda: open_explorer("output")).pack(side="left", padx=4)
ttk.Button(button_frame, text="Open markdown", command=lambda: open_markdown("output")).pack(side="left", padx=4)
```

After successful generation, replace the old done message/log line with:

```python
self.log(completion_message("output"))
```

or, if your GUI writes directly to a text box:

```python
self.output_text.insert("end", completion_message("output") + "\\n")
```

Optional success popup:

```python
from tkinter import messagebox
messagebox.showinfo("HADocs", completion_message("output"))
```

## Goal

The user should not have to manually find files after generation.
