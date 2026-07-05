from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk, messagebox

from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)


DEFAULT_CONFIG_PATH = Path("config.json")


@dataclass
class DesktopConfig:
    home_assistant_url: str = "http://homeassistant.local:8123"
    token: str = ""
    project_name: str = "My Smart Home"
    output_dir: str = "output"
    open_dashboard_after_scan: bool = True
    check_updates: bool = False


def load_desktop_config(path: str | Path = DEFAULT_CONFIG_PATH) -> DesktopConfig:
    path = Path(path)
    if not path.exists():
        return DesktopConfig()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DesktopConfig()

    return DesktopConfig(
        home_assistant_url=data.get("home_assistant_url")
        or data.get("url")
        or DesktopConfig.home_assistant_url,
        token=data.get("token", ""),
        project_name=data.get("project_name")
        or data.get("project")
        or DesktopConfig.project_name,
        output_dir=data.get("output_dir", "output"),
        open_dashboard_after_scan=bool(data.get("open_dashboard_after_scan", True)),
        check_updates=bool(data.get("check_updates", False)),
    )


def save_desktop_config(config: DesktopConfig, path: str | Path = DEFAULT_CONFIG_PATH) -> None:
    path = Path(path)
    data = {
        "home_assistant_url": config.home_assistant_url,
        "token": config.token,
        "project_name": config.project_name,
        "output_dir": config.output_dir,
        "open_dashboard_after_scan": config.open_dashboard_after_scan,
        "check_updates": config.check_updates,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class FirstRunWizard(tk.Toplevel):
    def __init__(self, master, config: DesktopConfig, on_finish):
        super().__init__(master)
        self.title("Welcome to HADocs")
        self.geometry("620x420")
        self.resizable(False, False)
        self.config_data = config
        self.on_finish = on_finish
        self.step = 0

        self.url_var = tk.StringVar(value=config.home_assistant_url)
        self.token_var = tk.StringVar(value=config.token)
        self.project_var = tk.StringVar(value=config.project_name)

        self.body = ttk.Frame(self, padding=24)
        self.body.pack(fill="both", expand=True)

        self.button_bar = ttk.Frame(self, padding=(24, 0, 24, 24))
        self.button_bar.pack(fill="x")

        self.back_button = ttk.Button(self.button_bar, text="Back", command=self.back)
        self.back_button.pack(side="left")

        self.next_button = ttk.Button(self.button_bar, text="Next", command=self.next)
        self.next_button.pack(side="right")

        self.render()

    def clear(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()
        self.back_button["state"] = "normal" if self.step > 0 else "disabled"

        if self.step == 0:
            ttk.Label(self.body, text="Welcome to HADocs", font=("Segoe UI", 24, "bold")).pack(anchor="w")
            ttk.Label(
                self.body,
                text="Let's connect your Home Assistant and generate your first smart home report.",
                wraplength=540,
            ).pack(anchor="w", pady=(16, 0))
            ttk.Label(
                self.body,
                text="HADocs is local-first. No telemetry. No cloud upload. No AI calls.",
                wraplength=540,
            ).pack(anchor="w", pady=(20, 0))
            self.next_button["text"] = "Next"

        elif self.step == 1:
            ttk.Label(self.body, text="Home Assistant connection", font=("Segoe UI", 18, "bold")).pack(anchor="w")
            form = ttk.Frame(self.body)
            form.pack(fill="x", pady=20)
            form.columnconfigure(1, weight=1)

            ttk.Label(form, text="Home Assistant URL").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=8)
            ttk.Entry(form, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", pady=8)

            ttk.Label(form, text="Long-Lived Token").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=8)
            ttk.Entry(form, textvariable=self.token_var, show="*").grid(row=1, column=1, sticky="ew", pady=8)

            ttk.Label(
                self.body,
                text="Create a Long-Lived Access Token in Home Assistant under your user profile.",
                wraplength=540,
            ).pack(anchor="w")
            self.next_button["text"] = "Next"

        else:
            ttk.Label(self.body, text="Project", font=("Segoe UI", 18, "bold")).pack(anchor="w")
            form = ttk.Frame(self.body)
            form.pack(fill="x", pady=20)
            form.columnconfigure(1, weight=1)

            ttk.Label(form, text="Project name").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=8)
            ttk.Entry(form, textvariable=self.project_var).grid(row=0, column=1, sticky="ew", pady=8)

            ttk.Label(
                self.body,
                text="You are ready. Click Finish to save settings and start using HADocs.",
                wraplength=540,
            ).pack(anchor="w")
            self.next_button["text"] = "Finish"

    def back(self):
        if self.step > 0:
            self.step -= 1
            self.render()

    def next(self):
        if self.step < 2:
            self.step += 1
            self.render()
            return

        self.config_data.home_assistant_url = self.url_var.get().strip()
        self.config_data.token = self.token_var.get().strip()
        self.config_data.project_name = self.project_var.get().strip() or "My Smart Home"
        save_desktop_config(self.config_data)
        self.on_finish(self.config_data)
        self.destroy()


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, config: DesktopConfig, on_save):
        super().__init__(master)
        self.title("HADocs Settings")
        self.geometry("640x460")
        self.config_data = config
        self.on_save = on_save

        self.url_var = tk.StringVar(value=config.home_assistant_url)
        self.token_var = tk.StringVar(value=config.token)
        self.project_var = tk.StringVar(value=config.project_name)
        self.output_var = tk.StringVar(value=config.output_dir)
        self.auto_open_var = tk.BooleanVar(value=config.open_dashboard_after_scan)
        self.update_var = tk.BooleanVar(value=config.check_updates)

        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Settings", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        fields = [
            ("Home Assistant URL", self.url_var, False),
            ("Long-Lived Token", self.token_var, True),
            ("Project name", self.project_var, False),
            ("Output folder", self.output_var, False),
        ]

        for idx, (label, var, secret) in enumerate(fields, start=1):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w", padx=(0, 10), pady=6)
            ttk.Entry(frame, textvariable=var, show="*" if secret else "").grid(row=idx, column=1, sticky="ew", pady=6)

        ttk.Checkbutton(frame, text="Open dashboard after scan", variable=self.auto_open_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=(18, 4))
        ttk.Checkbutton(frame, text="Check for updates on startup", variable=self.update_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=8, column=0, columnspan=2, sticky="e", pady=(24, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save", command=self.save).pack(side="right")

    def save(self):
        self.config_data.home_assistant_url = self.url_var.get().strip()
        self.config_data.token = self.token_var.get().strip()
        self.config_data.project_name = self.project_var.get().strip() or "My Smart Home"
        self.config_data.output_dir = self.output_var.get().strip() or "output"
        self.config_data.open_dashboard_after_scan = bool(self.auto_open_var.get())
        self.config_data.check_updates = bool(self.update_var.get())
        save_desktop_config(self.config_data)
        self.on_save(self.config_data)
        self.destroy()


class AboutDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("About HADocs")
        self.geometry("460x320")
        self.resizable(False, False)

        try:
            from src.hadocs.version import __version__
        except Exception:
            __version__ = "unknown"

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="HADocs", font=("Segoe UI", 26, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Smart Home Intelligence for Home Assistant").pack(anchor="w", pady=(4, 16))
        ttk.Label(frame, text=f"Version {__version__}").pack(anchor="w")
        ttk.Label(frame, text="Local-first • Privacy-first • AI-compatible").pack(anchor="w", pady=(16, 0))
        ttk.Label(frame, text="MIT License").pack(anchor="w", pady=(16, 0))
        ttk.Label(frame, text="GitHub: https://github.com/SirBlondieDK/HADocs", wraplength=390).pack(anchor="w", pady=(16, 0))
        ttk.Button(frame, text="Close", command=self.destroy).pack(anchor="e", pady=(26, 0))


class HADocsDesktopApp(ttk.Frame):
    def __init__(self, master, run_generate_callback=None, config_path: str | Path = DEFAULT_CONFIG_PATH):
        super().__init__(master, padding=16)
        self.master = master
        self.run_generate_callback = run_generate_callback
        self.config_path = Path(config_path)
        self.config_data = load_desktop_config(self.config_path)

        self.url_var = tk.StringVar(value=self.config_data.home_assistant_url)
        self.token_var = tk.StringVar(value=self.config_data.token)
        self.project_var = tk.StringVar(value=self.config_data.project_name)

        self.pack(fill="both", expand=True)
        self.build_ui()

        if not self.config_path.exists():
            self.after(300, self.show_wizard)

    def build_ui(self):
        self.master.title("HADocs - Smart Home Intelligence")
        self.master.geometry("1100x780")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="HA", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ttk.Label(header, text="HADocs", font=("Segoe UI", 24, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Smart Home Intelligence for Home Assistant").grid(row=1, column=1, sticky="w")

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for text, command in [
            ("🚀 Scan", self.generate),
            ("📊 Dashboard", lambda: open_dashboard(self.config_data.output_dir)),
            ("🧭 Explorer", lambda: open_explorer(self.config_data.output_dir)),
            ("📄 Markdown", lambda: open_markdown(self.config_data.output_dir)),
            ("📁 Output", lambda: open_output_folder(self.config_data.output_dir)),
            ("⚙ Settings", self.show_settings),
            ("❓ About", self.show_about),
        ]:
            ttk.Button(toolbar, text=text, command=command).pack(side="left", padx=(0, 8))

        connection = ttk.LabelFrame(self, text="Connection", padding=12)
        connection.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        connection.columnconfigure(1, weight=1)

        ttk.Label(connection, text="Home Assistant URL").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(connection, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(connection, text="Token").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(connection, textvariable=self.token_var, show="*").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(connection, text="Project name").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(connection, textvariable=self.project_var).grid(row=2, column=1, sticky="ew", pady=4)

        status = ttk.LabelFrame(self, text="Status", padding=12)
        status.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        status.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(status, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.log = tk.Text(self, height=18, wrap="word")
        self.log.grid(row=4, column=0, sticky="nsew")

        output = ttk.LabelFrame(self, text="Generated output", padding=12)
        output.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        for text, command in [
            ("Open Dashboard", lambda: open_dashboard(self.config_data.output_dir)),
            ("Open Explorer", lambda: open_explorer(self.config_data.output_dir)),
            ("Open Output Folder", lambda: open_output_folder(self.config_data.output_dir)),
        ]:
            ttk.Button(output, text=text, command=command).pack(side="left", padx=(0, 8))

    def write_log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def sync_config_from_fields(self):
        self.config_data.home_assistant_url = self.url_var.get().strip()
        self.config_data.token = self.token_var.get().strip()
        self.config_data.project_name = self.project_var.get().strip() or "My Smart Home"
        save_desktop_config(self.config_data, self.config_path)

    def generate(self):
        self.sync_config_from_fields()
        self.status_label["text"] = "Running scan..."
        self.progress["value"] = 5
        self.write_log("Starting HADocs scan...")

        steps = [
            (15, "Reading Home Assistant..."),
            (35, "Collecting devices and entities..."),
            (55, "Analyzing health and root causes..."),
            (75, "Generating dashboard and Explorer..."),
            (95, "Writing Knowledge Pack..."),
        ]
        for value, message in steps:
            self.progress["value"] = value
            self.write_log(message)
            self.update_idletasks()

        try:
            if self.run_generate_callback:
                self.run_generate_callback(
                    self.config_data.home_assistant_url,
                    self.config_data.token,
                    self.config_data.project_name,
                )

            self.progress["value"] = 100
            self.status_label["text"] = "Finished"
            msg = completion_message(self.config_data.output_dir)
            self.write_log("")
            self.write_log(msg)

            if self.config_data.open_dashboard_after_scan:
                open_dashboard(self.config_data.output_dir)

            messagebox.showinfo("HADocs", msg)

        except Exception as exc:
            self.status_label["text"] = "Error"
            self.write_log(f"ERROR: {exc}")
            messagebox.showerror("HADocs error", str(exc))

    def show_wizard(self):
        FirstRunWizard(self.master, self.config_data, self.apply_config)

    def show_settings(self):
        SettingsDialog(self.master, self.config_data, self.apply_config)

    def show_about(self):
        AboutDialog(self.master)

    def apply_config(self, config: DesktopConfig):
        self.config_data = config
        self.url_var.set(config.home_assistant_url)
        self.token_var.set(config.token)
        self.project_var.set(config.project_name)
        self.write_log("Settings saved.")


def run_desktop_gui(run_generate_callback=None):
    root = tk.Tk()
    HADocsDesktopApp(root, run_generate_callback=run_generate_callback)
    root.mainloop()
