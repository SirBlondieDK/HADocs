import tkinter as tk
from tkinter import ttk
from src.hadocs.gui.assets import load_logo_image
from src.hadocs.gui.theme import Theme
from src.hadocs.utils.config import save_config

class FirstRunWizard(tk.Toplevel):
    def __init__(self, master, cfg, on_finish):
        super().__init__(master)
        self.title("Welcome to HADocs")
        self.geometry("760x540")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        Theme.apply(self)

        self.cfg = dict(cfg)
        self.on_finish = on_finish
        self.step = 0

        self.url_var = tk.StringVar(value=self.cfg.get("ha_url", "http://homeassistant.local:8123"))
        self.token_var = tk.StringVar(value=self.cfg.get("token", ""))
        self.project_var = tk.StringVar(value=self.cfg.get("project_name", "My Smart Home"))

        container = ttk.Frame(self, style="Panel.TFrame", padding=28)
        container.pack(fill="both", expand=True)

        self.body = ttk.Frame(container, style="Panel.TFrame")
        self.body.pack(fill="both", expand=True)

        self.buttons = ttk.Frame(container, style="Panel.TFrame")
        self.buttons.pack(fill="x", pady=(20, 0))

        self.back_btn = ttk.Button(self.buttons, text="Back", command=self.back)
        self.back_btn.pack(side="left")

        self.next_btn = ttk.Button(self.buttons, text="Get Started", style="Accent.TButton", command=self.next)
        self.next_btn.pack(side="right")

        self.render()

    def clear(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()
        self.back_btn.config(state="normal" if self.step > 0 else "disabled")

        if self.step == 0:
            logo = load_logo_image(180)
            if logo is not None:
                label = ttk.Label(self.body, image=logo, style="Panel.TLabel")
                label.image = logo
                label.pack(anchor="center", pady=(0, 12))

            ttk.Label(self.body, text="Welcome to HADocs", style="Hero.TLabel").pack(anchor="center")
            ttk.Label(self.body, text="Understand your Home Assistant like never before.", style="MutedPanel.TLabel").pack(anchor="center", pady=(8, 22))

            features = [
                "✓ Health Score",
                "✓ Root Cause Analysis",
                "✓ AI-compatible Knowledge Pack",
                "✓ Local-first",
                "✓ No cloud upload",
                "✓ 100% private",
            ]
            ttk.Label(self.body, text="\n".join(features), style="Panel.TLabel", font=("Segoe UI", 12)).pack(anchor="center")
            self.next_btn.config(text="Get Started")

        elif self.step == 1:
            ttk.Label(self.body, text="Connect to Home Assistant", style="Hero.TLabel").pack(anchor="w")
            ttk.Label(self.body, text="Enter your URL and Long-Lived Access Token.", style="MutedPanel.TLabel").pack(anchor="w", pady=(8, 20))

            form = ttk.Frame(self.body, style="Panel.TFrame")
            form.pack(fill="x")
            form.columnconfigure(1, weight=1)

            ttk.Label(form, text="Home Assistant URL", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=8)
            ttk.Entry(form, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", pady=8)

            ttk.Label(form, text="Long-Lived Token", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=8)
            ttk.Entry(form, textvariable=self.token_var, show="*").grid(row=1, column=1, sticky="ew", pady=8)
            self.next_btn.config(text="Next")

        else:
            ttk.Label(self.body, text="Name your smart home", style="Hero.TLabel").pack(anchor="w")
            ttk.Label(self.body, text="Choose the name shown in generated reports.", style="MutedPanel.TLabel").pack(anchor="w", pady=(8, 20))

            form = ttk.Frame(self.body, style="Panel.TFrame")
            form.pack(fill="x")
            form.columnconfigure(1, weight=1)

            ttk.Label(form, text="Project name", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=8)
            ttk.Entry(form, textvariable=self.project_var).grid(row=0, column=1, sticky="ew", pady=8)
            self.next_btn.config(text="Finish")

    def back(self):
        if self.step > 0:
            self.step -= 1
            self.render()

    def next(self):
        if self.step < 2:
            self.step += 1
            self.render()
            return

        self.cfg["ha_url"] = self.url_var.get().strip()
        self.cfg["token"] = self.token_var.get().strip()
        self.cfg["project_name"] = self.project_var.get().strip() or "My Smart Home"
        save_config(self.cfg)
        self.on_finish(self.cfg)
        self.destroy()


