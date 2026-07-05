
from pathlib import Path

APP = Path("src/hadocs/gui/app.py")


def replace_function(text: str, name: str, new_block: str) -> str:
    marker = f"def {name}("
    start = text.find(marker)
    if start == -1:
        raise RuntimeError(f"Could not find function {name}")
    next_def = text.find("\ndef ", start + 1)
    next_class = text.find("\nclass ", start + 1)
    candidates = [x for x in (next_def, next_class) if x != -1]
    end = min(candidates) if candidates else len(text)
    return text[:start] + new_block.rstrip() + "\n\n" + text[end:].lstrip("\n")


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


LOGO_BLOCK = '''
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


def load_logo_image(max_size=170):
    LOGO_DEBUG.clear()
    path = find_logo_file()
    if path is None:
        LOGO_DEBUG.append("Logo not found in docs/images")
        return None

    LOGO_DEBUG.append(f"Logo file: {path}")

    try:
        from PIL import Image, ImageTk

        if path.suffix.lower() == ".svg":
            try:
                import io
                import cairosvg

                png_bytes = cairosvg.svg2png(url=str(path))
                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            except Exception as exc:
                LOGO_DEBUG.append(f"SVG render failed: {exc}")
                return None
        else:
            img = Image.open(path).convert("RGBA")

        img.thumbnail((max_size, max_size))
        canvas = Image.new("RGBA", (max_size, max_size), (0, 0, 0, 0))
        x = (max_size - img.width) // 2
        y = (max_size - img.height) // 2
        canvas.alpha_composite(img, (x, y))

        LOGO_DEBUG.append(f"Logo loaded with Pillow: {img.width}x{img.height}")
        return ImageTk.PhotoImage(canvas)
    except Exception as exc:
        LOGO_DEBUG.append(f"Pillow logo load failed: {exc}")

    if path.suffix.lower() == ".png":
        try:
            image = tk.PhotoImage(file=str(path))
            factor = max(1, int(max(image.width(), image.height()) / max_size))
            if factor > 1:
                image = image.subsample(factor, factor)
            LOGO_DEBUG.append(f"Logo loaded with Tk PhotoImage: {image.width()}x{image.height()}")
            return image
        except Exception as exc:
            LOGO_DEBUG.append(f"Tk logo load failed: {exc}")

    return None
'''


BUILD_SIDEBAR = '''
    def build_sidebar(self):
        self.sidebar = ttk.Frame(self.root_frame, style="Panel.TFrame", padding=(18, 22))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.configure(width=280)

        self.logo_image = load_logo_image(185)
        if self.logo_image is not None:
            logo_label = ttk.Label(self.sidebar, image=self.logo_image, style="Panel.TLabel")
            logo_label.pack(anchor="center", pady=(0, 12))
        else:
            ttk.Label(self.sidebar, text="HA", style="Panel.TLabel", font=("Segoe UI", 18, "bold")).pack(anchor="w")

        ttk.Label(
            self.sidebar,
            text="HADocs",
            style="Panel.TLabel",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="center" if self.logo_image else "w", pady=(4, 0))

        ttk.Label(
            self.sidebar,
            text="Smart Home Intelligence",
            style="MutedPanel.TLabel",
        ).pack(anchor="center" if self.logo_image else "w", pady=(0, 26))

        buttons = [
            ("🚀 Scan", self.run, "Accent.TButton"),
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
'''


BUILD_MAIN = '''
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
'''


BUILD_OUTPUT = '''
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
'''


BUILD_CONSOLE = '''
    def build_console(self):
        self.console_frame = ttk.LabelFrame(self.main, text="Developer log", padding=10)
        self.console_frame.grid(row=7, column=0, sticky="ew")
        self.console_frame.columnconfigure(0, weight=1)

        buttons = ttk.Frame(self.console_frame, style="Panel.TFrame")
        buttons.grid(row=0, column=0, sticky="w")

        ttk.Button(buttons, text="Open developer log", command=self.open_log_window).pack(side="left", padx=(0, 8))
        self.console_toggle = ttk.Button(buttons, text="Show inline log", command=self.toggle_console)
        self.console_toggle.pack(side="left")

        self.log = tk.Text(
            self.console_frame,
            height=8,
            wrap="word",
            bg="#020617",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Cascadia Mono", 10),
        )
        self.log.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.log_scroll = ttk.Scrollbar(self.console_frame, orient="vertical", command=self.log.yview)
        self.log_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.log.configure(yscrollcommand=self.log_scroll.set)

        self.log.grid_remove()
        self.log_scroll.grid_remove()
'''


def replace_logo_section(text: str) -> str:
    start = text.find("LOGO_DEBUG")
    if start != -1:
        # Replace from LOGO_DEBUG until safe_read_json or HealthGauge/class.
        markers = [
            text.find("\ndef safe_read_json", start),
            text.find("\nclass HealthGauge", start),
            text.find("\nclass FirstRunWizard", start),
        ]
        markers = [m for m in markers if m != -1]
        end = min(markers) if markers else start
        if end > start:
            return text[:start] + LOGO_BLOCK.rstrip() + "\n\n" + text[end:].lstrip("\n")

    if "def app_path(" in text:
        text = replace_function(text, "app_path", LOGO_BLOCK)
        if "def load_logo_image(" in text:
            text = replace_function(text, "load_logo_image", "")
        return text

    return LOGO_BLOCK.rstrip() + "\n\n" + text


def main():
    if not APP.exists():
        raise SystemExit("Run this from C:\\\\HomeAssistantDocs")

    text = APP.read_text(encoding="utf-8")
    text = replace_logo_section(text)
    text = replace_method(text, "App", "build_sidebar", BUILD_SIDEBAR)
    text = replace_method(text, "App", "build_main", BUILD_MAIN)
    text = replace_method(text, "App", "build_output_buttons", BUILD_OUTPUT)
    text = replace_method(text, "App", "build_console", BUILD_CONSOLE)

    if "Logo debug:" not in text:
        needle = 'self.log_msg("✓ Configuration looks valid")'
        if needle in text:
            replacement = '''self.log_msg("✓ Configuration looks valid")
            self.log_msg("Logo debug:")
            for line in LOGO_DEBUG:
                self.log_msg(f"- {line}")'''
            text = text.replace(needle, replacement, 1)

    APP.write_text(text, encoding="utf-8")
    print("Patched logo loading and layout.")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("Click Doctor if logo is still missing; it will print exact logo debug lines.")


if __name__ == "__main__":
    main()
