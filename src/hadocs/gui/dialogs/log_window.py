import tkinter as tk
from tkinter import ttk
from src.hadocs.gui.theme import COLORS, Theme

class LogWindow(tk.Toplevel):
    def __init__(self, master, source_text):
        super().__init__(master)
        self.title("HADocs Developer Log")
        self.geometry("950x600")
        self.transient(master)
        Theme.apply(self)

        frame = ttk.Frame(self, style="Panel.TFrame", padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.text = tk.Text(
            frame,
            wrap="none",
            bg="#020617",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Cascadia Mono", 10),
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")

        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.text.xview)
        xscroll.grid(row=1, column=0, sticky="ew")

        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.text.insert("1.0", source_text.get("1.0", "end-1c"))
        self.text.configure(state="disabled")

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))

        ttk.Button(buttons, text="Copy", command=self.copy_log).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="left")

    def copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end-1c"))

