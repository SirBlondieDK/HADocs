
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


def insert_before_class(text: str, class_name: str, block: str) -> str:
    marker = f"class {class_name}("
    pos = text.find(marker)
    if pos == -1:
        raise RuntimeError(f"Could not find class {class_name}")
    return text[:pos] + block.rstrip() + "\n\n" + text[pos:]


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


APP_PATH_BLOCK = '''
def app_path(*parts):
    import sys

    here = Path(__file__).resolve()
    candidates = [
        Path(getattr(sys, "_MEIPASS", Path.cwd())).joinpath(*parts),
        Path.cwd().joinpath(*parts),
    ]

    for parent in here.parents:
        candidates.append(parent.joinpath(*parts))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return Path.cwd().joinpath(*parts)
'''


LOGO_BLOCK = '''
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
'''


LOG_WINDOW_BLOCK = '''
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
'''


BUILD_CONSOLE_BLOCK = '''
    def build_console(self):
        self.console_frame = ttk.LabelFrame(self.main, text="Developer log", padding=10)
        self.console_frame.grid(row=6, column=0, sticky="ew", pady=(0, 14))
        self.console_frame.columnconfigure(0, weight=1)

        buttons = ttk.Frame(self.console_frame, style="Panel.TFrame")
        buttons.grid(row=0, column=0, sticky="w")

        ttk.Button(buttons, text="Open developer log", command=self.open_log_window).pack(side="left", padx=(0, 8))
        self.console_toggle = ttk.Button(buttons, text="Show inline log", command=self.toggle_console)
        self.console_toggle.pack(side="left")

        self.log = tk.Text(
            self.console_frame,
            height=10,
            wrap="word",
            bg="#020617",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Cascadia Mono", 10),
        )
        self.log.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self.log_scroll = ttk.Scrollbar(self.console_frame, orient="vertical", command=self.log.yview)
        self.log_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.log.configure(yscrollcommand=self.log_scroll.set)

        self.log.grid_remove()
        self.log_scroll.grid_remove()
'''


TOGGLE_BLOCK = '''
    def toggle_console(self):
        if self.console_visible:
            self.log.grid_remove()
            self.log_scroll.grid_remove()
            self.console_toggle.config(text="Show inline log")
            self.console_visible = False
        else:
            self.log.grid()
            self.log_scroll.grid()
            self.console_toggle.config(text="Hide inline log")
            self.console_visible = True

    def open_log_window(self):
        LogWindow(self, self.log)
'''


def main():
    if not APP.exists():
        raise SystemExit("Run from repository root: C:\\\\HomeAssistantDocs")

    text = APP.read_text(encoding="utf-8")

    if "def app_path(" in text:
        text = replace_function(text, "app_path", APP_PATH_BLOCK)

    if "def load_logo_image(" in text:
        text = replace_function(text, "load_logo_image", LOGO_BLOCK)
    else:
        text = insert_before_class(text, "HealthGauge", LOGO_BLOCK)

    if "class LogWindow(" not in text:
        text = insert_before_class(text, "FirstRunWizard", LOG_WINDOW_BLOCK)

    text = replace_method(text, "App", "build_console", BUILD_CONSOLE_BLOCK)
    text = replace_method(text, "App", "toggle_console", TOGGLE_BLOCK)

    if "Logo asset:" not in text:
        needle = 'self.log_msg("✓ Configuration looks valid")'
        if needle in text:
            replacement = '''self.log_msg("✓ Configuration looks valid")
            logo_path = find_logo_file()
            self.log_msg(f"Logo asset: {logo_path if logo_path else 'not found'}")'''
            text = text.replace(needle, replacement, 1)

    APP.write_text(text, encoding="utf-8")
    print("Patched src/hadocs/gui/app.py")
    print("Now run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("Then click Doctor to see the logo path.")


if __name__ == "__main__":
    main()
