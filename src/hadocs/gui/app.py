import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.reports.generator import generate_all
from src.hadocs.utils.config import load_config, save_config


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HADocs")
        self.geometry("900x660")
        self.cfg = load_config()
        frm = ttk.Frame(self, padding=12); frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Home Assistant URL").grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(frm, width=80); self.url.insert(0, self.cfg.get("ha_url", "")); self.url.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(frm, text="Token").grid(row=1, column=0, sticky="w")
        self.token = ttk.Entry(frm, width=80, show="*"); self.token.insert(0, self.cfg.get("token", "")); self.token.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(frm, text="Project name").grid(row=2, column=0, sticky="w")
        self.project = ttk.Entry(frm, width=80); self.project.insert(0, self.cfg.get("project_name", "Det Lille Hjem")); self.project.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        btns = ttk.Frame(frm); btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        self.run_btn = ttk.Button(btns, text="Generate documentation", command=self.run); self.run_btn.pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Open output", command=self.open_output).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Save config", command=self.save).pack(side="left")
        self.progress = ttk.Progressbar(frm, mode="indeterminate"); self.progress.grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
        self.log = tk.Text(frm, height=30); self.log.grid(row=5, column=0, columnspan=2, sticky="nsew")
        frm.columnconfigure(1, weight=1); frm.rowconfigure(5, weight=1)

    def get_cfg(self):
        return {"ha_url": self.url.get().strip(), "token": self.token.get().strip(), "project_name": self.project.get().strip() or "Home Assistant", "output_dir": "output", "cache_dir": "cache"}

    def save(self):
        save_config(self.get_cfg()); messagebox.showinfo("Saved", "config.json saved.")

    def log_msg(self, msg):
        self.log.insert("end", str(msg) + "\n"); self.log.see("end"); self.update_idletasks()

    def run(self):
        self.save(); self.run_btn.config(state="disabled"); self.progress.start(10); self.log.delete("1.0", "end"); threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            cfg = self.get_cfg(); data = collect_all(cfg, log=self.log_msg); idx = build_indexes(data); generate_all(data, idx, cfg, log=self.log_msg); self.log_msg("Done ✅")
        except Exception as exc:
            self.log_msg(f"ERROR: {exc}"); messagebox.showerror("Error", str(exc))
        finally:
            self.progress.stop(); self.run_btn.config(state="normal")

    def open_output(self):
        out = Path("output").resolve(); out.mkdir(exist_ok=True); webbrowser.open(str(out))


def run_gui():
    App().mainloop()
