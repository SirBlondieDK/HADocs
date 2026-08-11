from __future__ import annotations

from hadocs.gui import theme as theme_module
from hadocs.gui.theme import COLORS, Theme


class FakeRoot:
    def __init__(self):
        self.configuration = {}
        self.options = {}

    def configure(self, **kwargs):
        self.configuration.update(kwargs)

    def option_add(self, pattern, value):
        self.options[pattern] = value


class FakeStyle:
    def __init__(self):
        self.theme = None
        self.configurations = {}
        self.mappings = {}

    def theme_use(self, name):
        self.theme = name

    def configure(self, name, **kwargs):
        self.configurations[name] = kwargs

    def map(self, name, **kwargs):
        self.mappings[name] = kwargs


def test_windows_collection_widgets_have_explicit_dark_contrast(monkeypatch):
    root = FakeRoot()
    style = FakeStyle()
    monkeypatch.setattr(theme_module.ttk, "Style", lambda supplied_root: style)

    Theme.apply(root)

    tree = style.configurations["Treeview"]
    assert tree["background"] == "#020617"
    assert tree["fieldbackground"] == "#020617"
    assert tree["foreground"] == COLORS["text"]

    tree_states = style.mappings["Treeview"]
    assert tree_states["background"] == [("selected", "#075985")]
    assert tree_states["foreground"] == [("selected", "#f8fafc")]

    heading = style.configurations["Treeview.Heading"]
    assert heading["background"] == COLORS["panel2"]
    assert heading["foreground"] == COLORS["text"]

    combo = style.configurations["TCombobox"]
    assert combo["fieldbackground"] == "#020617"
    assert combo["foreground"] == COLORS["text"]
    assert combo["arrowcolor"] == COLORS["text"]

    combo_states = style.mappings["TCombobox"]
    assert ("readonly", "#020617") in combo_states["fieldbackground"]
    assert ("readonly", COLORS["text"]) in combo_states["foreground"]

    assert root.options["*TCombobox*Listbox.background"] == "#020617"
    assert root.options["*TCombobox*Listbox.foreground"] == COLORS["text"]
    assert root.options["*TCombobox*Listbox.selectBackground"] == "#075985"
    assert root.options["*TCombobox*Listbox.selectForeground"] == "#f8fafc"
