from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)


class HADocsModernApp(ttk.Frame):
    """Modern GUI shell for HADocs.

    This class is intentionally a GUI foundation. It can be wired into the
    existing generation function without changing the analysis engine.
    """

    def __init__(self, master, run_generate_callback=None, output_dir="output"):
        super().__init__(master, padding=18)
        self.master = master
        self.run_generate_callback = run_generate_callback
        self.output_dir = output_dir

        self.url_var = tk.StringVar(value="http://homeassistant.local:8123")
        self.token_var = tk.StringVar()
        self.project_var = tk.StringVar(value="My Smart Home")
        self.auto_open_var = tk.BooleanVar(value=True)

        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.master.title("HADocs - Smart Home Intelligence")
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(1, weight=1)

        logo = ttk.Label(header, text="HA", font=("Segoe UI", 18, "bold"))
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 12))

        ttk.Label(header, text="HADocs", font=("Segoe UI", 22, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Smart Home Intelligence for Home Assistant").grid(row=1, column=1, sticky="w")

        form = ttk.LabelFrame(self, text="Connection", padding=14)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Home Assistant URL").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Long-Lived Token").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.token_var, show="*").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Project name").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.project_var).grid(row=2, column=1, sticky="ew", pady=4)

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(actions, text="🚀 Generate Documentation", command=self.generate).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(actions, text="Open dashboard automatically", variable=self.auto_open_var).pack(side="left")

        progress_box = ttk.LabelFrame(self, text="Progress", padding=14)
        progress_box.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        progress_box.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_box, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew")

        self.log = tk.Text(self, height=16, wrap="word")
        self.log.grid(row=4, column=0, sticky="nsew", pady=(0, 12))
        self.rowconfigure(4, weight=1)

        output = ttk.LabelFrame(self, text="Output", padding=14)
        output.grid(row=5, column=0, sticky="ew")
        for label, command in [
            ("📊 Open Dashboard", lambda: open_dashboard(self.output_dir)),
            ("🧭 Open Explorer", lambda: open_explorer(self.output_dir)),
            ("📄 Open Markdown", lambda: open_markdown(self.output_dir)),
            ("📁 Open Output Folder", lambda: open_output_folder(self.output_dir)),
        ]:
            ttk.Button(output, text=label, command=command).pack(side="left", padx=(0, 8))

    def write_log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def generate(self):
        self.progress["value"] = 5
        self.write_log("Starting HADocs scan...")

        try:
            if self.run_generate_callback:
                self.run_generate_callback(
                    self.url_var.get(),
                    self.token_var.get(),
                    self.project_var.get(),
                )
            self.progress["value"] = 100
            msg = completion_message(self.output_dir)
            self.write_log("")
            self.write_log(msg)
            messagebox.showinfo("HADocs", msg)
            if self.auto_open_var.get():
                open_dashboard(self.output_dir)
        except Exception as exc:
            messagebox.showerror("HADocs error", str(exc))
            self.write_log(f"ERROR: {exc}")


def run_modern_gui(run_generate_callback=None, output_dir="output"):
    root = tk.Tk()
    root.geometry("980x760")
    HADocsModernApp(root, run_generate_callback=run_generate_callback, output_dir=output_dir)
    root.mainloop()
