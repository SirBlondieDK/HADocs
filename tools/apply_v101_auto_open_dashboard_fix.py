
from __future__ import annotations

from pathlib import Path

APP = Path("src/hadocs/gui/app.py")


def main():
    if not APP.exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    text = APP.read_text(encoding="utf-8")

    old = '''            if self.cfg.get("open_dashboard_after_scan", True):
                open_dashboard(cfg.get("output_dir", "output"))'''

    old2 = '''            if self.cfg.get("open_dashboard_after_scan", True):
                open_dashboard(self.cfg.get("output_dir", "output"))'''

    new = '''            if cfg.get("open_dashboard_after_scan", True):
                self.after(250, lambda: open_dashboard(cfg.get("output_dir", "output")))'''

    if old in text:
        text = text.replace(old, new, 1)
    elif old2 in text:
        text = text.replace(old2, new, 1)
    elif 'open_dashboard_after_scan' in text and 'open_dashboard(' in text:
        text = text.replace('if self.cfg.get("open_dashboard_after_scan", True):', 'if cfg.get("open_dashboard_after_scan", True):', 1)
        text = text.replace('open_dashboard(cfg.get("output_dir", "output"))', 'self.after(250, lambda: open_dashboard(cfg.get("output_dir", "output")))', 1)
    else:
        raise SystemExit("Could not find auto-open dashboard block in app.py")

    APP.write_text(text, encoding="utf-8")

    print("Auto-open dashboard fix applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Then check:")
    print("  Settings -> Open dashboard after scan must be checked")
    print("  Press Scan Home Assistant")
    print("")
    print("Commit:")
    print("  git add src/hadocs/gui/app.py docs/V101_AUTO_OPEN_DASHBOARD_FIX.md tools/apply_v101_auto_open_dashboard_fix.py")
    print('  git commit -m "Fix dashboard auto-open after scan"')
    print("  git push")


if __name__ == "__main__":
    main()
