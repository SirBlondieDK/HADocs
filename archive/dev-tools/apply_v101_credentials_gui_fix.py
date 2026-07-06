
from pathlib import Path

APP = Path("src/hadocs/gui/app.py")
CONFIG = Path("src/hadocs/utils/config.py")


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


def replace_top_function(text: str, name: str, new_block: str) -> str:
    marker = f"def {name}("
    start = text.find(marker)
    if start == -1:
        raise RuntimeError(f"Could not find {name}")

    next_def = text.find("\ndef ", start + 1)
    next_class = text.find("\nclass ", start + 1)
    candidates = [x for x in (next_def, next_class) if x != -1]
    end = min(candidates) if candidates else len(text)

    return text[:start] + new_block.rstrip() + "\n\n" + text[end:].lstrip("\n")


def ensure_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text

    lines = text.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


CONFIG_IMPORT = "from src.hadocs.security.credential_store import inject_token_into_runtime_config, migrate_plaintext_token_from_config"

LOAD_CONFIG = '''
def load_config():
    if not CONFIG_FILE.exists():
        return inject_token_into_runtime_config(DEFAULT_CONFIG)

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return inject_token_into_runtime_config(DEFAULT_CONFIG)

    merged = dict(DEFAULT_CONFIG)
    merged.update(config or {})
    return inject_token_into_runtime_config(merged)
'''

SAVE_CONFIG = '''
def save_config(config):
    clean = migrate_plaintext_token_from_config(config)
    clean = dict(clean or {})
    clean.pop("token", None)
    clean.pop("ha_token", None)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)
'''

SETTINGS_INIT = '''
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
'''

SETTINGS_SAVE = '''
    def save(self):
        token = self.token_var.get().strip()

        try:
            from src.hadocs.security.credential_store import set_home_assistant_token
            if token:
                set_home_assistant_token(token)
        except Exception as exc:
            messagebox.showerror("HADocs", f"Could not save token in Windows Credential Manager:\\n{exc}")
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
            messagebox.showerror("HADocs", f"Could not remove token from Windows Credential Manager:\\n{exc}")
            return

        self.token_var.set("")
        self.token_status.config(text="Token removed from Windows Credential Manager")
'''

APP_GET_CFG = '''
    def get_cfg(self):
        self.cfg.update({
            "ha_url": self.cfg.get("ha_url", ""),
            "project_name": self.cfg.get("project_name", "My Smart Home"),
            "output_dir": self.cfg.get("output_dir", "output"),
            "cache_dir": self.cfg.get("cache_dir", "cache"),
        })
        self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)
        return dict(self.cfg)
'''


def patch_config():
    if not CONFIG.exists():
        raise SystemExit("Missing src/hadocs/utils/config.py")

    text = CONFIG.read_text(encoding="utf-8")
    text = ensure_import(text, CONFIG_IMPORT)

    if "def load_config(" in text:
        text = replace_top_function(text, "load_config", LOAD_CONFIG)
    if "def save_config(" in text:
        text = replace_top_function(text, "save_config", SAVE_CONFIG)

    CONFIG.write_text(text, encoding="utf-8")
    print("Patched config.py")


def patch_app():
    if not APP.exists():
        raise SystemExit("Missing src/hadocs/gui/app.py")

    text = APP.read_text(encoding="utf-8")
    text = replace_method(text, "SettingsDialog", "__init__", SETTINGS_INIT)
    text = replace_method(text, "SettingsDialog", "save", SETTINGS_SAVE)
    text = replace_method(text, "App", "get_cfg", APP_GET_CFG)
    APP.write_text(text, encoding="utf-8")
    print("Patched app.py")


def main():
    patch_config()
    patch_app()

    print("")
    print("Now run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Manual check after saving Settings:")
    print("  cmdkey /list | findstr /i HADocs")
    print("  findstr /i token config.json")
    print("")
    print("Expected:")
    print("  cmdkey finds HADocs/HomeAssistantToken")
    print("  config.json does NOT contain token")
    print("")
    print("Commit:")
    print("  git add src/hadocs/utils/config.py src/hadocs/gui/app.py docs/CREDENTIALS_GUI_FIX.md tools/apply_v101_credentials_gui_fix.py")
    print('  git commit -m "Ensure token is stored in Windows Credential Manager"')
    print("  git push")


if __name__ == "__main__":
    main()
