from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class PatchWatchException(Exception):
    """Base exception for PatchWatch application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(PatchWatchException):
    """Authentication related exceptions."""
    pass


class AuthorizationException(PatchWatchException):
    """Authorization related exceptions."""
    pass


class ValidationException(PatchWatchException):
    """Validation related exceptions."""
    pass


class ResourceNotFoundException(PatchWatchException):
    """Resource not found exceptions."""
    pass


class ExternalAPIException(PatchWatchException):
    """External API related exceptions."""
    pass


class ScanException(PatchWatchException):
    """Scan processing related exceptions."""
    pass


# HTTP Exception factories
def http_401_unauthorized(message: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_403_forbidden(message: str = "Not authorized") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    )


def http_404_not_found(message: str = "Resource not found") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=message,
    )


def http_400_bad_request(message: str = "Bad request") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


def http_422_validation_error(message: str = "Validation error", details: Optional[Dict[str, Any]] = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"message": message, "details": details or {}},
    )


def http_500_internal_error(message: str = "Internal server error") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    )