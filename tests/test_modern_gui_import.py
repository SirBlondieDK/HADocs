def test_modern_gui_imports():
    from src.hadocs.gui.modern_app import HADocsModernApp, run_modern_gui

    assert HADocsModernApp is not None
    assert run_modern_gui is not None
