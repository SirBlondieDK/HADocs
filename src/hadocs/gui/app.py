import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from src.hadocs.gui.assets import app_path, load_logo_image
from src.hadocs.gui.data import read_latest_summary, safe_read_json
from src.hadocs.gui.theme import Theme
from src.hadocs.gui.dialogs.about_dialog import AboutDialog
from src.hadocs.gui.dialogs.first_run import FirstRunWizard
from src.hadocs.gui.dialogs.settings_dialog import SettingsDialog
from src.hadocs.gui.widgets.health_gauge import HealthGauge
from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.gui.assets import LOGO_DEBUG, find_logo_file, load_logo_image
from src.hadocs.gui.data import read_latest_summary
from src.hadocs.gui.dialogs.about_dialog import AboutDialog
from src.hadocs.gui.dialogs.device_override_manager import DeviceOverrideManager
from src.hadocs.gui.dialogs.first_run import FirstRunWizard
from src.hadocs.gui.dialogs.log_window import LogWindow
from src.hadocs.gui.dialogs.settings_dialog import SettingsDialog
from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)
from src.hadocs.gui.theme import COLORS, Theme
from src.hadocs.gui.widgets.health_gauge import HealthGauge
from src.hadocs.reports.generator import generate_all
from src.hadocs.utils.config import (
    config_exists,
    load_config,
    save_config,
    validate_config,
    validate_config_warnings,
)
from src.hadocs.utils.security import (
    gitignore_contains_required_entries,
    tracked_generated_files,
    tracked_sensitive_files,
)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        Theme.apply(self)

        self.title("HADocs - Smart Home Intelligence")
        self.geometry("1320x920")
        self.minsize(1100, 780)
        self.cfg = load_config()
        self.logo_image = None
        self.console_visible = False
        self.last_scan_time = None

        self.root_frame = ttk.Frame(self, style="Panel.TFrame")
        self.root_frame.pack(fill="both", expand=True)
        self.root_frame.columnconfigure(1, weight=1)
        self.root_frame.rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main()
        self.refresh_summary_from_disk()

        if not config_exists():
            self.after(250, self.open_first_run_wizard)



    def build_sidebar(self):
        self.sidebar = ttk.Frame(self.root_frame, style="Panel.TFrame", padding=(18, 22))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.configure(width=280)

        self.logo_image = load_logo_image(155)
        if self.logo_image is not None:
            logo_label = ttk.Label(self.sidebar, image=self.logo_image, style="Panel.TLabel")
            logo_label.pack(anchor="center", pady=(0, 8))
        else:
            ttk.Label(
                self.sidebar,
                text="HA",
                style="Panel.TLabel",
                font=("Segoe UI", 18, "bold"),
            ).pack(anchor="center", pady=(0, 8))

        ttk.Label(
            self.sidebar,
            text="HADocs",
            style="Panel.TLabel",
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="center", pady=(0, 2))

        ttk.Label(
            self.sidebar,
            text="Smart Home Intelligence",
            style="MutedPanel.TLabel",
        ).pack(anchor="center", pady=(0, 28))

        buttons = [
            ("🚀 Scan Home Assistant", self.run, "Accent.TButton"),
            ("📊 Dashboard", lambda: open_dashboard(self.cfg.get("output_dir", "output")), None),
            ("🧭 Explorer", lambda: open_explorer(self.cfg.get("output_dir", "output")), None),
            ("🧩 Device Overrides", self.open_device_overrides, None),
            ("📄 Markdown", lambda: open_markdown(self.cfg.get("output_dir", "output")), None),
            ("📁 Output Folder", lambda: open_output_folder(self.cfg.get("output_dir", "output")), None),
            ("🩺 Doctor", self.run_doctor, None),
            ("⚙ Settings", self.open_settings, None),
            ("❓ About", lambda: AboutDialog(self), None),
        ]

        for text, command, style in buttons:
            kwargs = {"text": text, "command": command}
            if style:
                kwargs["style"] = style
            btn = ttk.Button(self.sidebar, **kwargs)
            btn.pack(fill="x", pady=5)
            if text.startswith("🚀"):
                self.run_btn = btn

        ttk.Label(self.sidebar, text="Local only • No cloud", style="MutedPanel.TLabel").pack(
            anchor="w", side="bottom", pady=(30, 0)
        )

    def open_device_overrides(self):
        DeviceOverrideManager(self, self.cfg)

    def build_main(self):
        self.main = ttk.Frame(self.root_frame, style="Panel.TFrame", padding=24)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.columnconfigure(0, weight=1)

        self.hero_title = ttk.Label(
            self.main,
            text=self.cfg.get("project_name", "My Smart Home"),
            style="Hero.TLabel",
        )
        self.hero_title.grid(row=0, column=0, sticky="w")

        self.hero_subtitle = ttk.Label(
            self.main,
            text="Smart dashboard for your local Home Assistant intelligence report.",
            style="HeroSub.TLabel",
        )
        self.hero_subtitle.grid(row=1, column=0, sticky="w", pady=(0, 18))

        self.build_smart_dashboard()
        self.build_connection_summary()
        self.build_status()
        self.build_output_buttons()
        self.build_console()


    def build_smart_dashboard(self):
        smart = ttk.Frame(self.main, style="Panel.TFrame")
        smart.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        smart.columnconfigure(0, weight=2)
        smart.columnconfigure(1, weight=3)

        self.health_card = ttk.Frame(smart, style="Card.TFrame", padding=18)
        self.health_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.health_card.columnconfigure(0, weight=1)

        ttk.Label(self.health_card, text="♡ Health Score", style="MutedCard.TLabel").grid(row=0, column=0, sticky="w")
        self.health_gauge = HealthGauge(self.health_card, size=184)
        self.health_gauge.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.health_status_label = ttk.Label(self.health_card, text="Waiting for first scan.", style="MutedCard.TLabel")
        self.health_status_label.grid(row=2, column=0, sticky="w", pady=(4, 0))

        self.health_potential_label = ttk.Label(self.health_card, text="Potential: —", style="MutedCard.TLabel")
        self.health_potential_label.grid(row=3, column=0, sticky="w", pady=(12, 0))

        self.recommendation_card = ttk.Frame(smart, style="Card.TFrame", padding=18)
        self.recommendation_card.grid(row=0, column=1, sticky="nsew")
        self.recommendation_card.columnconfigure(0, weight=1)

        ttk.Label(self.recommendation_card, text="💡 Top Recommendation", style="MutedCard.TLabel").grid(row=0, column=0, sticky="w")
        self.recommendation_title = ttk.Label(self.recommendation_card, text="No scan yet", style="Card.TLabel", font=("Segoe UI", 23, "bold"))
        self.recommendation_title.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.recommendation_meta = ttk.Label(
            self.recommendation_card,
            text="Generate documentation to see the highest-impact action.",
            style="MutedCard.TLabel",
            wraplength=680,
        )
        self.recommendation_meta.grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.top_issues_label = ttk.Label(
            self.recommendation_card,
            text="Top issues will appear here after a scan.",
            style="MutedCard.TLabel",
            wraplength=680,
        )
        self.top_issues_label.grid(row=3, column=0, sticky="w", pady=(16, 0))

        ttk.Button(
            self.recommendation_card,
            text="Open Dashboard",
            style="Accent.TButton",
            command=lambda: open_dashboard(self.cfg.get("output_dir", "output")),
        ).grid(row=4, column=0, sticky="w", pady=(18, 0))

        metrics = ttk.Frame(self.main, style="Panel.TFrame")
        metrics.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        for col in range(5):
            metrics.columnconfigure(col, weight=1)

        self.metric_status = self.metric_card(metrics, "Ready", "● Status")
        self.metric_entities = self.metric_card(metrics, "—", "⚡ Entities")
        self.metric_devices = self.metric_card(metrics, "—", "◈ Devices")
        self.metric_integrations = self.metric_card(metrics, "—", "⌁ Integrations")
        self.metric_root_causes = self.metric_card(metrics, "—", "⚠ Root causes")

        for i, card in enumerate(
            [
                self.metric_status,
                self.metric_entities,
                self.metric_devices,
                self.metric_integrations,
                self.metric_root_causes,
            ]
        ):
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

    def metric_card(self, master, value, label):
        card = ttk.Frame(master, style="Card.TFrame", padding=16)
        value_label = ttk.Label(card, text=value, style="MetricValue.TLabel")
        value_label.pack(anchor="w")
        ttk.Label(card, text=label, style="MetricLabel.TLabel").pack(anchor="w", pady=(4, 0))
        return card

    def set_metric(self, card, value):
        card.winfo_children()[0].config(text=str(value))

    def build_connection_summary(self):
        self.connection_card = ttk.Frame(self.main, style="Card.TFrame", padding=16)
        self.connection_card.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        self.connection_card.columnconfigure(0, weight=1)

        ttk.Label(self.connection_card, text="Project", style="MutedCard.TLabel").grid(row=0, column=0, sticky="w")
        self.connection_details = ttk.Label(self.connection_card, text=self.connection_summary_text(), style="Card.TLabel", font=("Segoe UI", 12))
        self.connection_details.grid(row=1, column=0, sticky="w", pady=(6, 0))

        ttk.Button(self.connection_card, text="Edit Settings", command=self.open_settings).grid(row=0, column=1, rowspan=2, sticky="e")


    def connection_summary_text(self):
        url = self.cfg.get("ha_url", "Not configured")
        project = self.cfg.get("project_name", "My Smart Home")

        try:
            from src.hadocs.security.credential_store import get_home_assistant_token
            token = get_home_assistant_token()
        except Exception:
            token = None

        token_state = "🔒 Token saved" if token else "⚠ Token missing"
        last = f"Last scan: {self.last_scan_time}" if self.last_scan_time else "Last scan: Never"
        return f"{project}\n{url}\n{token_state}\n{last}"

    def update_connection_summary(self):
        self.connection_details.config(text=self.connection_summary_text())

    def build_status(self):
        status = ttk.LabelFrame(self.main, text="Scan status", padding=14)
        status.grid(row=5, column=0, sticky="ew", pady=(0, 14))
        status.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(status, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(10, 0))




    def build_console(self):
        self.console_frame = ttk.LabelFrame(self.main, text="Developer log", padding=10)
        self.console_frame.grid(row=7, column=0, sticky="ew")
        self.console_frame.columnconfigure(0, weight=1)

        ttk.Button(
            self.console_frame,
            text="Open developer log",
            command=self.open_log_window,
        ).grid(row=0, column=0, sticky="w")

        self.log = tk.Text(
            self.console_frame,
            height=1,
            wrap="word",
            bg="#020617",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Cascadia Mono", 10),
        )
        self.log.grid_remove()


    def toggle_console(self):
        self.open_log_window()

    def open_log_window(self):
        LogWindow(self, self.log)


    def build_output_buttons(self):
        output = ttk.LabelFrame(self.main, text="Generated output", padding=14)
        output.grid(row=6, column=0, sticky="ew", pady=(0, 14))
        ttk.Button(
            output,
            text="Open Dashboard",
            style="Accent.TButton",
            command=lambda: open_dashboard(self.cfg.get("output_dir", "output")),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            output,
            text="Open Explorer",
            command=lambda: open_explorer(self.cfg.get("output_dir", "output")),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            output,
            text="Open Markdown",
            command=lambda: open_markdown(self.cfg.get("output_dir", "output")),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            output,
            text="Open Output Folder",
            command=lambda: open_output_folder(self.cfg.get("output_dir", "output")),
        ).pack(side="left", padx=(0, 8))

    def refresh_summary_from_disk(self):
        data = read_latest_summary(self.cfg.get("output_dir", "output"))
        self.apply_summary(data)

    def apply_summary(self, data):
        health = data.get("health", {})
        inventory = data.get("inventory", {})
        recommendations = data.get("recommendations", [])
        incidents = data.get("incidents", [])

        health_score = health.get("health_score")
        potential = health.get("potential_score")
        status = health.get("status")

        if health_score is not None:
            self.health_gauge.set_score(health_score)
            self.health_status_label.config(text=str(status or "Health calculated"))
            self.health_potential_label.config(text=f"Potential: {potential}" if potential is not None else "Potential: —")

        self.set_metric(self.metric_entities, inventory.get("entities", "—"))
        self.set_metric(self.metric_devices, inventory.get("devices", inventory.get("physical_devices", "—")))
        self.set_metric(self.metric_integrations, inventory.get("integrations", "—"))
        self.set_metric(self.metric_root_causes, len(incidents) if incidents else "—")

        if recommendations:
            top = recommendations[0]
            title = top.get("title", "Top recommendation")
            gain = top.get("estimated_score_gain", 0)
            minutes = top.get("estimated_repair_minutes", 0)
            reason = top.get("reason", "")
            self.recommendation_title.config(text=title)
            self.recommendation_meta.config(text=f"+{gain} Health Score • ~{minutes} min\n{reason}")

        if incidents:
            items = []
            for incident in incidents[:3]:
                root = incident.get("root_cause") or incident.get("title") or "Issue"
                severity = str(incident.get("severity") or "").upper()
                affected = len(incident.get("affected_entities", []) or [])
                icon = "🔴" if severity == "CRITICAL" else "🟠" if severity in {"WARNING", "WARN"} else "🟡"
                items.append(f"{icon} {root} — {affected} affected")
            self.top_issues_label.config(text="\n".join(items))

    def apply_cfg_to_fields(self):
        self.hero_title.config(text=self.cfg.get("project_name", "My Smart Home"))
        self.update_connection_summary()



    def get_cfg(self):
        cfg = dict(self.cfg or {})

        cfg["ha_url"] = cfg.get("ha_url", "")
        cfg["project_name"] = cfg.get("project_name", "My Smart Home")
        cfg["output_dir"] = cfg.get("output_dir", "output")
        cfg["cache_dir"] = cfg.get("cache_dir", "cache")
        cfg["open_dashboard_after_scan"] = bool(cfg.get("open_dashboard_after_scan", True))

        try:
            from src.hadocs.security.credential_store import get_home_assistant_token
            token = get_home_assistant_token()
        except Exception:
            token = None

        if token:
            cfg["token"] = token
        else:
            cfg.pop("token", None)
            cfg.pop("ha_token", None)

        return cfg

    def log_msg(self, msg):
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")
        self.update_idletasks()

    def run_doctor(self):
        save_config(self.get_cfg())
        self.log.delete("1.0", "end")
        if not self.console_visible:
            self.toggle_console()

        cfg = self.get_cfg()
        problems = validate_config(cfg)
        warnings = validate_config_warnings(cfg)

        for warning in warnings:
            self.log_msg(f"WARNING: {warning}")
        if problems:
            self.log_msg("Configuration problems:")
            for problem in problems:
                self.log_msg(f"- {problem}")
            self.set_metric(self.metric_status, "Issues")
        else:
            self.log_msg("✓ Configuration looks valid")
            self.log_msg("Logo debug:")
            for line in LOGO_DEBUG:
                self.log_msg(f"- {line}")
            logo_path = find_logo_file()
            self.log_msg(f"Logo asset: {logo_path if logo_path else 'not found'}")

        tracked = tracked_sensitive_files()
        generated = tracked_generated_files()

        if tracked:
            self.log_msg("✗ Sensitive files tracked by Git:")
            for file in tracked:
                self.log_msg(f"- {file}")
        else:
            self.log_msg("✓ No sensitive files tracked by Git")

        if generated:
            self.log_msg("✗ Generated files tracked by Git:")
            for file in generated:
                self.log_msg(f"- {file}")
        else:
            self.log_msg("✓ No generated files tracked by Git")

        ok, missing = gitignore_contains_required_entries()
        if ok:
            self.log_msg("✓ .gitignore safety entries found")
            self.set_metric(self.metric_status, "Ready")
        else:
            self.log_msg("✗ Missing .gitignore entries:")
            for item in missing:
                self.log_msg(f"- {item}")
            self.set_metric(self.metric_status, "Issues")


    def run(self):
        save_config(self.get_cfg())
        self.run_btn.config(state="disabled", text="⟳ Scanning...")
        self.progress.config(value=5)
        self.status_label.config(text="Connecting...")
        self.set_metric(self.metric_status, "Scanning")
        self.log.delete("1.0", "end")
        threading.Thread(target=self.worker, daemon=True).start()

    def set_progress(self, value, message=None):
        self.progress.config(value=value)
        if message:
            self.status_label.config(text=message)
            self.log_msg(message)

    def worker(self):
        try:
            cfg = self.get_cfg()
            problems = validate_config(cfg)
            warnings = validate_config_warnings(cfg)

            for warning in warnings:
                self.log_msg(f"WARNING: {warning}")
            if problems:
                for problem in problems:
                    self.log_msg(f"ERROR: {problem}")
                self.set_metric(self.metric_status, "Error")
                return

            self.set_progress(10, "Connecting to Home Assistant...")
            self.set_progress(20, "Collecting devices, entities and states...")
            data = collect_all(cfg, log=self.log_msg)

            self.set_progress(45, "Building installation index...")
            idx = build_indexes(data)

            self.set_progress(65, "Analyzing health and root causes...")
            self.set_progress(80, "Generating dashboard, Explorer and Knowledge Pack...")
            generate_all(data, idx, cfg, log=self.log_msg)

            self.set_progress(100, "Documentation generated successfully")
            self.set_metric(self.metric_status, "Done")
            self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.update_connection_summary()

            msg = completion_message(cfg.get("output_dir", "output"))
            self.log_msg("")
            self.log_msg(msg)

            self.refresh_summary_from_disk()

            if cfg.get("open_dashboard_after_scan", True):
                self.after(250, lambda: open_dashboard(cfg.get("output_dir", "output")))

            messagebox.showinfo("HADocs", msg)
        except Exception as exc:
            self.status_label.config(text="Error")
            self.set_metric(self.metric_status, "Error")
            self.log_msg(f"ERROR: {exc}")
            messagebox.showerror("Error", str(exc))
        finally:
            self.run_btn.config(state="normal", text="🚀 Scan Home Assistant")

    def open_settings(self):
        SettingsDialog(self, self.get_cfg(), self.on_settings_saved)


    def on_settings_saved(self, cfg):
        self.cfg = dict(cfg or {})
        self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)
        self.apply_cfg_to_fields()
        self.update_connection_summary()
        self.status_label.config(text="Settings saved")

    def open_first_run_wizard(self):
        FirstRunWizard(self, self.cfg, self.on_settings_saved)


def run_gui():
    App().mainloop()

# Backward-compatible public names used by modern_app.py and existing launchers.
HADocsModernApp = App
run_modern_gui = run_gui
HADocsDesktopApp = App
run_desktop_gui = run_gui
