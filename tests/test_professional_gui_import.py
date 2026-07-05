def test_professional_gui_imports():
    from src.hadocs.gui.app import App, Theme, FirstRunWizard, SettingsDialog, AboutDialog, run_gui

    assert Theme is not None
    assert App is not None
    assert FirstRunWizard is not None
    assert SettingsDialog is not None
    assert AboutDialog is not None
    assert run_gui is not None
