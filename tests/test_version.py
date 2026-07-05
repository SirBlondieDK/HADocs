from src.hadocs.version import __version__, APP_NAME, APP_DESCRIPTION


def test_version_metadata():
    assert __version__ == "0.16.0"
    assert APP_NAME == "HADocs"
    assert "Home Assistant" in APP_DESCRIPTION
