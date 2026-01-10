"""API layer exceptions.

Lightweight exceptions without Home Assistant dependencies.
The coordinator layer wraps these in translatable HA exceptions.
"""

from __future__ import annotations


class GoveeApiError(Exception):
    """Base exception for Govee API errors."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class GoveeAuthError(GoveeApiError):
    """Authentication failed - invalid API key or credentials."""

    def __init__(self, message: str = "Invalid API key") -> None:
        super().__init__(message, code=401)


class GoveeRateLimitError(GoveeApiError):
    """Rate limit exceeded - too many requests."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, code=429)
        self.retry_after = retry_after


class GoveeConnectionError(GoveeApiError):
    """Network or connection error."""

    def __init__(self, message: str = "Failed to connect to Govee API") -> None:
        super().__init__(message)


class GoveeDeviceNotFoundError(GoveeApiError):
    """Device not found (expected for group devices)."""

    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device not found: {device_id}", code=400)
        self.device_id = device_id
