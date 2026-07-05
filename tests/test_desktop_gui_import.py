def test_desktop_gui_import():
    from src.hadocs.gui.desktop_app import HADocsDesktopApp, FirstRunWizard, SettingsDialog, AboutDialog

    assert HADocsDesktopApp is not None
    assert FirstRunWizard is not None
    assert SettingsDialog is not None
    assert AboutDialog is not None
