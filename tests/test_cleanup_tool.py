from pathlib import Path

import tools_cleanup


def test_cleanup_remove_dir(tmp_path):
    folder = tmp_path / ".pytest_tmp"
    folder.mkdir()
    assert tools_cleanup.remove_dir(folder) is True
    assert not folder.exists()


def test_cleanup_missing_dir(tmp_path):
    folder = tmp_path / "missing"
    assert tools_cleanup.remove_dir(folder) is False
