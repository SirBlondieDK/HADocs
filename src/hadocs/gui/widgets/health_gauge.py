import tkinter as tk
from src.hadocs.gui.theme import COLORS

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



