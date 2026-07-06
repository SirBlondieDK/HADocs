from pathlib import Path
import re


def test_readme_mentions_images():
    text = Path("README.md").read_text(encoding="utf-8")

    images = re.findall(
        r"assets/screenshots/[A-Za-z0-9_-]+\.png",
        text,
    )

    assert len(set(images)) >= 6
