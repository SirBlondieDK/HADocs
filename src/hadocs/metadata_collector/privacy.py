"""Fail-closed privacy infrastructure from the frozen privacy model."""

from __future__ import annotations

from enum import Enum
from typing import Callable

from .errors import PrivacyError


class PrivacyClass(str, Enum):
    PUBLIC = "PUBLIC"
    LOCAL = "LOCAL"
    SENSITIVE = "SENSITIVE"
    SECRET = "SECRET"


class PrivacyTransformer:
    def __init__(self, opaque_reference: Callable[[str], str] | None = None) -> None:
        self._opaque_reference = opaque_reference

    def transform_identifier(self, value: str, classification: PrivacyClass) -> str:
        if classification in {PrivacyClass.PUBLIC, PrivacyClass.LOCAL}:
            return value
        if classification is PrivacyClass.SECRET:
            raise PrivacyError("secret_value_prohibited")
        if self._opaque_reference is None:
            raise PrivacyError("opaque_reference_not_configured")
        transformed = self._opaque_reference(value)
        if not transformed or transformed == value:
            raise PrivacyError("unsafe_opaque_reference")
        return transformed

