"""Closed infrastructure errors for the frozen collector contract."""


class CollectorError(Exception):
    """Base error that carries a safe, contract-facing code."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class ContractVersionError(CollectorError):
    pass


class RegistrationError(CollectorError):
    pass


class PrivacyError(CollectorError):
    pass


class LifecycleError(CollectorError):
    pass

