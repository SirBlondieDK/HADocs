from __future__ import annotations

from getpass import getpass

from src.hadocs.platform import MigrationManager
from src.hadocs.utils.config import (
    CONFIG_FILE,
    load_config,
    save_config,
)


class InitApplication:
    """Create or update the local HADocs configuration."""

    def run(self) -> int:
        print("HADocs setup")
        print("------------")

        migration = MigrationManager()
        result = migration.migrate()

        for message in result.messages:
            print(f"Migration: {message}")

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

        print()
        print(f"Configuration saved to: {CONFIG_FILE}")
        print("Run: hadocs doctor")

        return 0
