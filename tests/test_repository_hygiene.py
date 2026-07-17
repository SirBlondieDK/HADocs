from pathlib import Path


def test_gitignore_contains_user_configuration():
    content = Path(".gitignore").read_text(encoding="utf-8")

    required_entries = {
        "config.json",
        "device_overrides.json",
        "device_overrides.local.json",
        "config/config.json",
        "config/device_overrides.json",
        "config/device_overrides.local.json",
    }

    missing = sorted(entry for entry in required_entries if entry not in content)

    assert not missing, f"Missing .gitignore entries: {missing}"