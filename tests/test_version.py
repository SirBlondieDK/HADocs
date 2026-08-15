from pathlib import Path

from hadocs.version import (
    APP_DESCRIPTION,
    APP_NAME,
    CORE,
    DOCKER,
    HOME_ASSISTANT_ADDON,
    RELEASE_CHANNEL,
    RELEASE_VERSION,
    WINDOWS,
    __version__,
)
from hadocs.web.app import HadocsRequestHandler, ScanManager


ROOT = Path(__file__).resolve().parents[1]


def test_version_metadata():
    assert RELEASE_VERSION == "0.17.0"
    assert RELEASE_CHANNEL == "rc3"
    assert __version__ == "0.17.0-rc3"
    assert __version__.replace("-", "") == "0.17.0rc3"
    assert APP_NAME == "HADocs"
    assert "Home Assistant" in APP_DESCRIPTION


def test_product_versions():
    assert WINDOWS.display_version == "0.17.0-rc3"
    assert CORE.display_version == "0.17.0-rc3"
    assert DOCKER.display_version == "0.17.0-rc3"
    assert HOME_ASSISTANT_ADDON.display_version == "0.17.0-rc3"


def test_distribution_and_web_versions_follow_product_authority():
    addon = (ROOT / "hadocs" / "config.yaml").read_text(encoding="utf-8")
    installer = (ROOT / "installer" / "HADocs.iss").read_text(encoding="utf-8")
    index = (
        ROOT / "src" / "hadocs" / "web" / "static" / "index.html"
    ).read_text(encoding="utf-8")
    script = (
        ROOT / "src" / "hadocs" / "web" / "static" / "app.js"
    ).read_text(encoding="utf-8")
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert f'version: "{__version__}"' in addon
    assert f'#define MyAppVersion "{__version__}"' in installer
    assert HadocsRequestHandler.server_version == f"HADocsWeb/{__version__}"
    assert ScanManager().status()["version"] == __version__

    assert 'id="app-version"' in index
    assert "version unavailable" in index
    assert __version__ not in index
    assert "status.version" in script
    assert 'version = {attr = "hadocs.version.__version__"}' in project
