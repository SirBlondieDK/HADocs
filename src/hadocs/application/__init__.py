from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hadocs.application.doctor import DoctorApplication
    from hadocs.application.generate import GenerateApplication
    from hadocs.application.init import InitApplication

_EXPORTS = {
    "DoctorApplication": "hadocs.application.doctor",
    "GenerateApplication": "hadocs.application.generate",
    "InitApplication": "hadocs.application.init",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load public application classes without creating import cycles."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
