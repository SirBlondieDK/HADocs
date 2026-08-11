import tkinter as tk
from tkinter import ttk

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
        style.configure(
            "Treeview",
            background="#020617",
            fieldbackground="#020617",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            rowheight=26,
        )
        style.map(
            "Treeview",
            background=[("selected", "#075985")],
            foreground=[("selected", "#f8fafc")],
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#1f2a44")],
            foreground=[("active", COLORS["text"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground="#020617",
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            selectbackground="#020617",
            selectforeground=COLORS["text"],
            padding=(8, 5),
        )
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", "#020617"),
                ("disabled", COLORS["panel2"]),
            ],
            foreground=[
                ("readonly", COLORS["text"]),
                ("disabled", COLORS["muted"]),
            ],
            selectbackground=[("readonly", "#020617")],
            selectforeground=[("readonly", COLORS["text"])],
            arrowcolor=[
                ("disabled", COLORS["muted"]),
                ("readonly", COLORS["text"]),
            ],
        )
        root.option_add("*TCombobox*Listbox.background", "#020617")
        root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        root.option_add("*TCombobox*Listbox.selectBackground", "#075985")
        root.option_add("*TCombobox*Listbox.selectForeground", "#f8fafc")
        style.configure("TButton", background=COLORS["panel2"], foreground=COLORS["text"], bordercolor=COLORS["border"], focusthickness=0, padding=(12, 7))
        style.map("TButton", background=[("active", "#1f2a44")])
        style.configure("Accent.TButton", background=COLORS["blue"], foreground="#020617", bordercolor=COLORS["blue"], font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.map("Accent.TButton", background=[("active", "#7dd3fc")])
        style.configure("Horizontal.TProgressbar", troughcolor="#020617", background=COLORS["green"], bordercolor=COLORS["border"])
