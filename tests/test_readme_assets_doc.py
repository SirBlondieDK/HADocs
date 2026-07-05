from pathlib import Path


def test_readme_mentions_images():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "docs/images/dashboard.png" in text
    assert "Privacy First" in text
    assert "AI-compatible" in text or "AI-compatible" in text
