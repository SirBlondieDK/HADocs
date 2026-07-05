def test_logo_and_log_imports():
    from src.hadocs.gui.app import LogWindow, find_logo_file, load_logo_image
    assert LogWindow is not None
    assert find_logo_file is not None
    assert load_logo_image is not None
