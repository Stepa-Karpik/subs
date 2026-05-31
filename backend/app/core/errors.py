from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "app_error", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401, code="unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403, code="forbidden")


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404, code="not_found")


class ValidationAppError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=422, code="validation_error", details=details)
