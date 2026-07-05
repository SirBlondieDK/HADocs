def test_gui_app_imports():
    from src.hadocs.gui.app import App, FirstRunWizard, SettingsDialog, AboutDialog, run_gui

    assert App is not None
    assert FirstRunWizard is not None
    assert SettingsDialog is not None
    assert AboutDialog is not None
    assert run_gui is not None
