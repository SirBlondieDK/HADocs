import json
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.gui.output_actions import (
    completion_message,
    open_dashboard,
    open_explorer,
    open_markdown,
    open_output_folder,
)
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


COLORS = {
    "bg": "#0b1020",
    "panel": "#111827",
    "panel2": "#172033",
    "card": "#0f172a",
    "border": "#263244",
    "text": "#e5e7eb",
    "muted": "#9ca3af",
    "blue": "#38bdf8",
    "green": "#22c55e",
    "yellow": "#facc15",
    "red": "#ef4444",
    "purple": "#a78bfa",
}




LOGO_DEBUG = []


def _project_roots():
    import sys

    roots = [
        Path(getattr(sys, "_MEIPASS", Path.cwd())),
        Path.cwd(),
    ]

    try:
        here = Path(__file__).resolve()
        roots.extend(here.parents)
    except Exception:
        pass

    unique = []
    seen = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except Exception:
            resolved = root
        if resolved not in seen:
            unique.append(root)
            seen.add(resolved)

    return unique


def app_path(*parts):
    for root in _project_roots():
        candidate = root.joinpath(*parts)
        if candidate.exists():
            return candidate
    return Path.cwd().joinpath(*parts)


def find_logo_file():
    names = [
        "logo.png",
        "Logo.png",
        "HADocs.png",
        "hadocs.png",
        "logo.svg",
        "icon.png",
        "Icon.png",
    ]

    for root in _project_roots():
        for name in names:
            candidate = root / "docs" / "images" / name
            if candidate.exists():
                return candidate

    for root in _project_roots():
        images = root / "docs" / "images"
        if not images.exists():
            continue
        try:
            matches = sorted(
                [
                    p
                    for p in images.iterdir()
                    if p.is_file()
                    and "logo" in p.name.lower()
                    and p.suffix.lower() in {".png", ".svg", ".gif"}
                ]
            )
            if matches:
                return matches[0]
        except Exception:
            continue

    return None




def safe_read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_latest_summary(output_dir):
    output = Path(output_dir)
    recommendations = safe_read_json(output / "knowledge" / "recommendations.json")
    incidents = safe_read_json(output / "knowledge" / "incidents.json")

    return {
        "health": safe_read_json(output / "knowledge" / "health.json"),
        "inventory": safe_read_json(output / "knowledge" / "inventory.json"),
        "recommendations": recommendations if isinstance(recommendations, list) else [],
        "incidents": incidents if isinstance(incidents, list) else [],
        "latest": safe_read_json(output / "history" / "latest.json"),
        "summary": safe_read_json(output / "history" / "summary.json"),
    }


class Theme:
    @staticmethod
    def apply(root):
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        root.configure(bg=COLORS["bg"])

        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("MutedPanel.TLabel", background=COLORS["panel"], foreground=COLORS["muted"])
        style.configure("Card.TLabel", background=COLORS["card"], foreground=COLORS["text"])
        style.configure("MutedCard.TLabel", background=COLORS["card"], foreground=COLORS["muted"])
        style.configure("Hero.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI", 30, "bold"))
        style.configure("HeroSub.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 11))
        style.configure("MetricValue.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=("Segoe UI", 28, "bold"))
        style.configure("MetricLabel.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["text"], bordercolor=COLORS["border"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#020617", foreground=COLORS["text"], insertcolor=COLORS["text"], bordercolor=COLORS["border"])
        style.configure("TButton", background=COLORS["panel2"], foreground=COLORS["text"], bordercolor=COLORS["border"], focusthickness=0, padding=(12, 7))
        style.map("TButton", background=[("active", "#1f2a44")])
        style.configure("Accent.TButton", background=COLORS["blue"], foreground="#020617", bordercolor=COLORS["blue"], font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.map("Accent.TButton", background=[("active", "#7dd3fc")])
        style.configure("Horizontal.TProgressbar", troughcolor="#020617", background=COLORS["green"], bordercolor=COLORS["border"])



def find_logo_file():
    direct = [
        app_path("docs", "images", "logo.png"),
        app_path("docs", "images", "Logo.png"),
        app_path("docs", "images", "logo.svg"),
        app_path("docs", "images", "icon.png"),
    ]

    for path in direct:
        if path.exists():
            return path

    roots = [Path.cwd()]
    try:
        roots.append(Path(__file__).resolve().parents[3])
    except Exception:
        pass

    wanted = {"logo.png", "Logo.png", "logo.svg", "icon.png"}
    for root in roots:
        try:
            for candidate in root.rglob("*"):
                if candidate.name in wanted and "docs" in candidate.parts and "images" in candidate.parts:
                    return candidate
        except Exception:
            continue

    return None


def load_logo_image(max_size=170):
    path = find_logo_file()
    if path is None:
        return None

    try:
        from PIL import Image, ImageTk

        if path.suffix.lower() == ".svg":
            try:
                import io
                import cairosvg

                png_bytes = cairosvg.svg2png(url=str(path))
                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            except Exception:
                return None
        else:
            img = Image.open(path).convert("RGBA")

        img.thumbnail((max_size, max_size))
        canvas = Image.new("RGBA", (max_size, max_size), (0, 0, 0, 0))
        x = (max_size - img.width) // 2
        y = (max_size - img.height) // 2
        canvas.alpha_composite(img, (x, y))
        return ImageTk.PhotoImage(canvas)
    except Exception:
        pass

    if path.suffix.lower() == ".png":
        try:
            image = tk.PhotoImage(file=str(path))
            factor = max(1, int(max(image.width(), image.height()) / max_size))
            if factor > 1:
                image = image.subsample(factor, factor)
            return image
        except Exception:
            return None

    return None

class HealthGauge(tk.Canvas):
    def __init__(self, master, size=184):
        super().__init__(master, width=size, height=size, bg=COLORS["card"], highlightthickness=0, bd=0)
        self.size = size
        self.score = None
        self.message = "CLICK SCAN"
        self.draw()

    def set_score(self, score):
        try:
            self.score = int(score)
            self.message = "HEALTH"
        except Exception:
            self.score = None
            self.message = "CLICK SCAN"
        self.draw()

    def draw(self):
        self.delete("all")
        pad = 18
        box = (pad, pad, self.size - pad, self.size - pad)
        self.create_arc(box, start=90, extent=-359.9, style="arc", width=16, outline="#263244")

        if self.score is not None:
            extent = -359.9 * max(0, min(100, self.score)) / 100
            color = COLORS["green"] if self.score >= 85 else COLORS["yellow"] if self.score >= 60 else COLORS["red"]
            self.create_arc(box, start=90, extent=extent, style="arc", width=16, outline=color)

        text = "—" if self.score is None else str(self.score)
        self.create_text(self.size / 2, self.size / 2 - 8, text=text, fill=COLORS["text"], font=("Segoe UI", 38, "bold"))
        self.create_text(self.size / 2, self.size / 2 + 31, text=self.message, fill=COLORS["muted"], font=("Segoe UI", 9, "bold"))



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

class AboutDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("About HADocs")
        self.geometry("540x450")
        self.resizable(False, False)
        self.transient(master)
        Theme.apply(self)

        try:
            from src.hadocs.version import __version__
        except Exception:
            __version__ = "unknown"

        frame = ttk.Frame(self, style="Panel.TFrame", padding=24)
        frame.pack(fill="both", expand=True)

        logo = load_logo_image(175)
        if logo is not None:
            label = ttk.Label(frame, image=logo, style="Panel.TLabel")
            label.image = logo
            label.pack(anchor="center", pady=(0, 10))

        ttk.Label(frame, text="HADocs", style="Hero.TLabel").pack(anchor="center")
        ttk.Label(frame, text="Smart Home Intelligence for Home Assistant", style="MutedPanel.TLabel").pack(anchor="center", pady=(4, 18))
        ttk.Label(frame, text=f"Version {__version__}", style="Panel.TLabel").pack(anchor="center")
        ttk.Label(frame, text="Local-first • Privacy-first • AI-compatible", style="Panel.TLabel").pack(anchor="center", pady=(16, 0))
        ttk.Label(frame, text="Built with ❤️ for the Home Assistant community.", style="MutedPanel.TLabel").pack(anchor="center", pady=(12, 0))
        ttk.Label(frame, text="MIT License", style="MutedPanel.TLabel").pack(anchor="center", pady=(12, 0))
        ttk.Label(frame, text="https://github.com/SirBlondieDK/HADocs", style="MutedPanel.TLabel", wraplength=450).pack(anchor="center", pady=(12, 0))
        ttk.Button(frame, text="Close", command=self.destroy).pack(anchor="center", pady=(18, 0))


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
