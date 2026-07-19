import tkinter as tk
from tkinter import ttk
from src.hadocs.gui.assets import load_logo_image
from src.hadocs.gui.theme import Theme

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


