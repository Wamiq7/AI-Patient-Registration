from typing import Any
from uuid import UUID


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class PatientNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="PATIENT_NOT_FOUND",
            message="Patient not found",
            status_code=404,
            details=None,
        )


class DuplicatePatientError(AppError):
    def __init__(self, patient_id: UUID) -> None:
        super().__init__(
            code="DUPLICATE_PATIENT",
            message="A patient with this phone number already exists.",
            status_code=409,
            details={"patient_id": str(patient_id)},
        )


class UnauthorizedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message="Invalid or missing API key",
            status_code=401,
            details=None,
        )


class DatabaseUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="DATABASE_UNAVAILABLE",
            message="Database connection failed",
            status_code=503,
            details=None,
        )
