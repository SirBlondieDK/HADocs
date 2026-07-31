from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile


# Keep routine test collection from repopulating the recovery worktree.
sys.dont_write_bytecode = True


def pytest_configure(config) -> None:
    if config.option.basetemp is None:
        config.option.basetemp = Path(tempfile.gettempdir()) / (
            f"hadocs-pytest-{os.getpid()}"
        )
