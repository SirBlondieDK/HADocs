
from pathlib import Path

APP = Path("src/hadocs/gui/app.py")


def replace_method(text: str, class_name: str, method_name: str, new_block: str) -> str:
    class_marker = f"class {class_name}("
    class_start = text.find(class_marker)
    if class_start == -1:
        raise RuntimeError(f"Could not find class {class_name}")

    next_class = text.find("\nclass ", class_start + 1)
    class_end = next_class if next_class != -1 else len(text)
    class_text = text[class_start:class_end]

    method_marker = f"    def {method_name}("
    method_start_rel = class_text.find(method_marker)
    if method_start_rel == -1:
        raise RuntimeError(f"Could not find {class_name}.{method_name}")

    method_start = class_start + method_start_rel
    next_method_rel = class_text.find("\n    def ", method_start_rel + 1)
    method_end = class_start + next_method_rel if next_method_rel != -1 else class_end

    return text[:method_start] + new_block.rstrip() + "\n\n" + text[method_end:].lstrip("\n")


BUILD_SIDEBAR = """
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
"""


BUILD_SMART_DASHBOARD = """
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
"""


BUILD_CONSOLE = """
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
"""


TOGGLE_CONSOLE = """
    def toggle_console(self):
        self.open_log_window()

    def open_log_window(self):
        LogWindow(self, self.log)
"""


RUN_METHOD = """
    def run(self):
        save_config(self.get_cfg())
        self.run_btn.config(state="disabled", text="⟳ Scanning...")
        self.progress.config(value=5)
        self.status_label.config(text="Connecting...")
        self.set_metric(self.metric_status, "Scanning")
        self.log.delete("1.0", "end")
        threading.Thread(target=self.worker, daemon=True).start()
"""


def main():
    if not APP.exists():
        raise SystemExit("Run this from C:\\HomeAssistantDocs")

    text = APP.read_text(encoding="utf-8")

    text = replace_method(text, "App", "build_sidebar", BUILD_SIDEBAR)
    text = replace_method(text, "App", "build_smart_dashboard", BUILD_SMART_DASHBOARD)
    text = replace_method(text, "App", "build_console", BUILD_CONSOLE)
    text = replace_method(text, "App", "toggle_console", TOGGLE_CONSOLE)
    text = replace_method(text, "App", "run", RUN_METHOD)

    text = text.replace(
        'self.run_btn.config(state="normal")',
        'self.run_btn.config(state="normal", text="🚀 Scan Home Assistant")',
    )

    APP.write_text(text, encoding="utf-8")
    print("Final sleep patch applied.")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("Push:")
    print("  git status")
    print("  git add .")
    print('  git commit -m "Polish desktop GUI final tweaks"')
    print("  git push")


if __name__ == "__main__":
    main()
