# API layer exceptions - lightweight without Home Assistant dependencies.
# The coordinator layer wraps these in translatable exceptions.
from __future__ import annotations


class GoveeApiError(Exception):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class GoveeAuthError(GoveeApiError):
    def __init__(self, message: str = "Invalid API key") -> None:
        super().__init__(message, code=401)


class GoveeRateLimitError(GoveeApiError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, code=429)
        self.retry_after = retry_after


class GoveeConnectionError(GoveeApiError):
    def __init__(self, message: str = "Failed to connect to Govee API") -> None:
        super().__init__(message)
