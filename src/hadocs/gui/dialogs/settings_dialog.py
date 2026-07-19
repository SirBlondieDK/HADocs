import tkinter as tk
from tkinter import ttk, messagebox
from src.hadocs.gui.theme import Theme
from src.hadocs.utils.config import save_config

class SettingsDialog(tk.Toplevel):

    def __init__(self, master, cfg, on_save):
        super().__init__(master)
        self.title("HADocs Settings")
        self.geometry("700x520")
        self.transient(master)
        Theme.apply(self)

        self.cfg = dict(cfg)
        self.on_save = on_save

        try:
            from src.hadocs.security.credential_store import get_home_assistant_token
            stored_token = get_home_assistant_token() or ""
        except Exception:
            stored_token = ""

        self.url_var = tk.StringVar(value=self.cfg.get("ha_url", ""))
        self.token_var = tk.StringVar(value=stored_token or self.cfg.get("token", ""))
        self.project_var = tk.StringVar(value=self.cfg.get("project_name", "My Smart Home"))
        self.output_var = tk.StringVar(value=self.cfg.get("output_dir", "output"))
        self.auto_open_var = tk.BooleanVar(value=bool(self.cfg.get("open_dashboard_after_scan", True)))

        frame = ttk.Frame(self, style="Panel.TFrame", padding=22)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Settings", style="Hero.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 22))

        rows = [
            ("Home Assistant URL", self.url_var, False),
            ("Home Assistant Token", self.token_var, True),
            ("Project name", self.project_var, False),
            ("Output folder", self.output_var, False),
        ]

        for idx, (label, var, secret) in enumerate(rows, start=1):
            ttk.Label(frame, text=label, style="Panel.TLabel").grid(row=idx, column=0, sticky="w", padx=(0, 12), pady=7)
            ttk.Entry(frame, textvariable=var, show="*" if secret else "").grid(row=idx, column=1, sticky="ew", pady=7)

        self.token_status = ttk.Label(
            frame,
            text="🔒 Stored in Windows Credential Manager" if stored_token else "Token will be stored securely in Windows",
            style="MutedPanel.TLabel",
        )
        self.token_status.grid(row=2, column=2, sticky="w", padx=(12, 0), pady=7)

        ttk.Button(frame, text="Forget token", command=self.forget_token).grid(row=5, column=1, sticky="w", pady=(8, 0))

        ttk.Checkbutton(frame, text="Open dashboard after scan", variable=self.auto_open_var).grid(row=6, column=0, columnspan=3, sticky="w", pady=(20, 4))

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.grid(row=7, column=0, columnspan=3, sticky="e", pady=(28, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=self.save).pack(side="right")


    def save(self):
        token = self.token_var.get().strip()

        try:
            from src.hadocs.security.credential_store import set_home_assistant_token
            if token:
                set_home_assistant_token(token)
        except Exception as exc:
            messagebox.showerror("HADocs", f"Could not save token in Windows Credential Manager:\n{exc}")
            return

        self.cfg["ha_url"] = self.url_var.get().strip()
        self.cfg["project_name"] = self.project_var.get().strip() or "My Smart Home"
        self.cfg["output_dir"] = self.output_var.get().strip() or "output"
        self.cfg["cache_dir"] = self.cfg.get("cache_dir", "cache")
        self.cfg["open_dashboard_after_scan"] = bool(self.auto_open_var.get())
        self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)

        save_config(self.cfg)
        self.on_save(self.cfg)
        self.destroy()

    def forget_token(self):
        try:
            from src.hadocs.security.credential_store import delete_home_assistant_token
            delete_home_assistant_token()
        except Exception as exc:
            messagebox.showerror("HADocs", f"Could not remove token from Windows Credential Manager:\n{exc}")
            return

        self.token_var.set("")
        self.token_status.config(text="Token removed from Windows Credential Manager")

