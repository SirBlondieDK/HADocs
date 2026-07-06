
from __future__ import annotations

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


GET_CFG = '''
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
'''


CONNECTION_SUMMARY_TEXT = '''
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
        return f"{project}\\n{url}\\n{token_state}\\n{last}"
'''


ON_SETTINGS_SAVED = '''
    def on_settings_saved(self, cfg):
        self.cfg = dict(cfg or {})
        self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)
        self.apply_cfg_to_fields()
        self.update_connection_summary()
        self.status_label.config(text="Settings saved")
'''


FIRST_RUN_FINISH = '''
    def finish(self):
        self.cfg["ha_url"] = self.url_var.get().strip()
        self.cfg["project_name"] = self.project_var.get().strip() or "My Smart Home"

        token = self.token_var.get().strip()
        if token:
            try:
                from src.hadocs.security.credential_store import set_home_assistant_token
                set_home_assistant_token(token)
            except Exception as exc:
                messagebox.showerror("HADocs", f"Could not save token in Windows Credential Manager:\\n{exc}")
                return

        self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)
        save_config(self.cfg)
        self.on_finish(self.cfg)
        self.destroy()
'''


RUN_DOCTOR_EXTRA = '''
            self.log_msg("Credential Manager:")
            try:
                from src.hadocs.security.credential_store import get_home_assistant_token
                self.log_msg("✓ Token found in Windows Credential Manager" if get_home_assistant_token() else "✗ Token not found in Windows Credential Manager")
            except Exception as exc:
                self.log_msg(f"✗ Credential Manager error: {exc}")
'''


def patch_run_doctor(text: str) -> str:
    if "Credential Manager:" in text:
        return text

    needle = 'self.log_msg("✓ Configuration looks valid")'
    if needle not in text:
        return text

    return text.replace(needle, needle + "\n" + RUN_DOCTOR_EXTRA.rstrip(), 1)


def main():
    if not APP.exists():
        raise SystemExit("Run from repository root: C:\\\\HomeAssistantDocs")

    text = APP.read_text(encoding="utf-8")

    text = replace_method(text, "App", "get_cfg", GET_CFG)
    text = replace_method(text, "App", "connection_summary_text", CONNECTION_SUMMARY_TEXT)
    text = replace_method(text, "App", "on_settings_saved", ON_SETTINGS_SAVED)

    if "class FirstRunWizard(" in text and "    def finish(" in text:
        text = replace_method(text, "FirstRunWizard", "finish", FIRST_RUN_FINISH)

    text = patch_run_doctor(text)

    APP.write_text(text, encoding="utf-8")

    print("Runtime token fix applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Manual test:")
    print("  1. Settings -> Save")
    print("  2. cmdkey /list | findstr /i HADocs")
    print("  3. findstr /i token config.json")
    print("  4. Scan")
    print("")
    print("Expected:")
    print("  - cmdkey shows HADocs/HomeAssistantToken")
    print("  - config.json has no token")
    print("  - Scan no longer says Token is missing")
    print("")
    print("Commit:")
    print("  git add src/hadocs/gui/app.py docs/V101_RUNTIME_TOKEN_FIX.md tools/apply_v101_runtime_token_fix.py")
    print('  git commit -m "Use Credential Manager token at scan runtime"')
    print("  git push")


if __name__ == "__main__":
    main()
