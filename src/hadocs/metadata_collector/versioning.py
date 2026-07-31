"""Contract-major negotiation for the DF-001 producer contract."""

from __future__ import annotations

from dataclasses import dataclass

from .contract import CONTRACT_NAME, CONTRACT_VERSION
from .errors import ContractVersionError


@dataclass(frozen=True, slots=True)
class ContractRegistration:
    name: str = CONTRACT_NAME
    version: str = CONTRACT_VERSION


class VersionNegotiator:
    def negotiate(self, requested_version: str) -> str:
        try:
            requested = tuple(int(part) for part in requested_version.split("."))
            supported = tuple(int(part) for part in CONTRACT_VERSION.split("."))
        except (AttributeError, ValueError) as exc:
            raise ContractVersionError("invalid_contract_version") from exc
        if len(requested) != 3 or requested[0] != supported[0]:
            raise ContractVersionError("unsupported_contract_major")
        return "exact" if requested == supported else "compatible_major"

    def registration(self) -> ContractRegistration:
        return ContractRegistration()

