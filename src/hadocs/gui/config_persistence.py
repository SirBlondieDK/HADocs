from __future__ import annotations

from collections.abc import Callable


CONFIG_SAVE_ERROR = (
    "HADocs could not save your settings. Check that the HADocs data folder "
    "is writable and that sufficient disk space is available, then try again."
)
CONFIG_CALLBACK_ERROR = (
    "Your settings were saved, but the HADocs window could not refresh. "
    "Close and restart HADocs to load the saved settings."
)


def try_save_config(
    config: dict,
    *,
    save: Callable[[dict], None],
) -> tuple[bool, str | None]:
    """Persist GUI settings and return only a secret-free user message."""

    try:
        save(config)
    except Exception:
        return False, CONFIG_SAVE_ERROR
    return True, None


def try_config_callback(
    config: dict,
    *,
    callback: Callable[[dict], None],
) -> tuple[bool, str | None]:
    """Run a post-save GUI callback without exposing exception details."""

    try:
        callback(config)
    except Exception:
        return False, CONFIG_CALLBACK_ERROR
    return True, None
