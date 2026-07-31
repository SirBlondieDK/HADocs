from hadocs.version import (
    APP_DESCRIPTION,
    APP_NAME,
    CORE,
    DOCKER,
    HOME_ASSISTANT_ADDON,
    WINDOWS,
    __version__,
)


def test_version_metadata():
    assert __version__ == "0.17.0-rc1"
    assert APP_NAME == "HADocs"
    assert "Home Assistant" in APP_DESCRIPTION


def test_product_versions():
    assert WINDOWS.display_version == "0.17.0-rc1"
    assert CORE.display_version == "0.17.0-rc1"
    assert DOCKER.display_version == "0.17.0-rc1"
    assert HOME_ASSISTANT_ADDON.display_version == "0.17.0-rc1"
