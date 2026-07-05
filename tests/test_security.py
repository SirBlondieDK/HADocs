from pathlib import Path

from src.hadocs.utils.security import gitignore_contains_required_entries


def test_gitignore_required_entries(tmp_path):
    (tmp_path / ".gitignore").write_text("config.json\nconfig.local.json\n.env\ncache/\noutput/\n*.zip\n")
    ok, missing = gitignore_contains_required_entries(str(tmp_path))
    assert ok
    assert missing == []
