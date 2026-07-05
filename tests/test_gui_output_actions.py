from pathlib import Path

from src.hadocs.gui.output_actions import completion_message, output_paths, output_status


def test_output_paths():
    paths = output_paths("output")
    assert paths["dashboard"] == Path("output") / "index.html"
    assert paths["explorer"] == Path("output") / "explorer" / "index.html"


def test_output_status_missing(tmp_path):
    status = output_status(tmp_path)
    assert status["dashboard"] is False
    assert status["explorer"] is False


def test_completion_message(tmp_path):
    (tmp_path / "explorer").mkdir()
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "index.html").write_text("html", encoding="utf-8")
    (tmp_path / "explorer" / "index.html").write_text("html", encoding="utf-8")
    (tmp_path / "index.md").write_text("md", encoding="utf-8")

    msg = completion_message(tmp_path)
    assert "Documentation successfully generated" in msg
    assert "Dashboard:" in msg
    assert "Explorer:" in msg
    assert "Knowledge Pack:" in msg
    assert "Markdown:" in msg
