class HaskDatabaseError(RuntimeError):
    """Base error for the isolated HASK database infrastructure."""


class FeatureDisabledError(HaskDatabaseError):
    """Raised when default-disabled infrastructure is invoked."""


class PragmaValidationError(HaskDatabaseError):
    """Raised when a mandatory SQLite runtime setting cannot be established."""


class IntegrityValidationError(HaskDatabaseError):
    """Raised when SQLite reports an integrity failure."""


class MigrationValidationError(HaskDatabaseError):
    """Raised when migration identity, order, checksum, or state is invalid."""


class SecretUnavailableError(HaskDatabaseError):
    """Raised when no approved protected secret provider is available."""


class RepositoryError(HaskDatabaseError):
    """Base class for canonical repository-boundary failures."""

    category = "REPOSITORY_ERROR"


class NotFoundError(RepositoryError): category = "NOT_FOUND"
class AlreadyExistsError(RepositoryError): category = "ALREADY_EXISTS"
class ConstraintViolationError(RepositoryError): category = "CONSTRAINT_VIOLATION"
class ValidationFailureError(RepositoryError): category = "VALIDATION_FAILURE"
class ConcurrencyConflictError(RepositoryError): category = "CONCURRENCY_CONFLICT"
class StorageFailureError(RepositoryError): category = "STORAGE_FAILURE"
class CorruptionDetectedError(RepositoryError): category = "CORRUPTION_DETECTED"
class RepositoryMigrationFailureError(RepositoryError): category = "MIGRATION_FAILURE"
class RepositorySecretUnavailableError(RepositoryError): category = "SECRET_UNAVAILABLE"
class BundleMismatchError(RepositoryError): category = "BUNDLE_MISMATCH"
class VersionIncompatibleError(RepositoryError): category = "VERSION_INCOMPATIBLE"
class IdempotencyConflictError(RepositoryError): category = "IDEMPOTENCY_CONFLICT"
class NestedTransactionError(ConcurrencyConflictError): pass
class RecoveryModeError(CorruptionDetectedError): pass
