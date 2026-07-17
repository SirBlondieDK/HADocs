from __future__ import annotations

from getpass import getpass

from src.hadocs.utils.config import load_config, save_config


class InitApplication:
    """Create or update the local HADocs configuration."""

    def run(self) -> int:
        print("HADocs setup")
        print("------------")

        cfg = load_config()

        cfg["ha_url"] = (
            input(f"Home Assistant URL [{cfg['ha_url']}]: ").strip()
            or cfg["ha_url"]
        )

        cfg["token"] = getpass("Long-Lived Access Token: ").strip()

        cfg["project_name"] = (
            input(f"Project name [{cfg['project_name']}]: ").strip()
            or cfg["project_name"]
        )

        save_config(cfg)

        print("")
        print("Saved config.json")
        print("Run: hadocs doctor")

        return 0
