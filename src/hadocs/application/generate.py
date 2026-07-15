from __future__ import annotations

from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.reports.generator import generate_all
from src.hadocs.utils.config import (
    load_config,
    validate_config,
    validate_config_warnings,
)


class GenerateApplication:
    """Run the complete HADocs documentation generation workflow."""

    def run(self) -> int:
        cfg = load_config()

        warnings = validate_config_warnings(cfg)
        for warning in warnings:
            print(f"WARNING: {warning}")

        problems = validate_config(cfg)
        if problems:
            print("Configuration problems:")
            for problem in problems:
                print(f"- {problem}")
            return 1

        data = collect_all(cfg)
        indexes = build_indexes(data)
        generate_all(data, indexes, cfg)

        return 0
