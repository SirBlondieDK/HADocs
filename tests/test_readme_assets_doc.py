from pathlib import Path


def test_readme_mentions_images():
    text = Path("README.md").read_text(encoding="utf-8")

    expected = [
        "assets/screenshots/01-dashboard-overview.png",
        "assets/screenshots/02-installation-overview.png",
        "assets/screenshots/03-top-recommendations.png",
        "assets/screenshots/04-root-cause-analysis.png",
        "assets/screenshots/05-health-score-history.png",
        "assets/screenshots/06-generated-output.png",
    ]

    for image in expected:
        assert image in text