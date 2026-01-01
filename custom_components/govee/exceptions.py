from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN


class GoveeException(HomeAssistantError):

    translation_domain: str = DOMAIN
    translation_key: str = "unknown_error"

    def __init__(
        self,
        translation_key: str | None = None,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        effective_key = translation_key if translation_key is not None else type(self).translation_key
        effective_placeholders = translation_placeholders or {}

        super().__init__(
            translation_domain=type(self).translation_domain,
            translation_key=effective_key,
            translation_placeholders=effective_placeholders,
        )


class GoveeAuthenticationError(GoveeException):

    translation_key = "authentication_failed"


class GoveeConnectionError(GoveeException):

    translation_key = "connection_failed"


class GoveeRateLimitError(GoveeException):

    translation_key = "rate_limit_exceeded"

    def __init__(self, retry_after: int | None = None) -> None:
        placeholders = {}
        if retry_after is not None:
            placeholders["retry_after"] = str(retry_after)
        else:
            placeholders["retry_after"] = "unknown"

        super().__init__(
            translation_key=self.translation_key,
            translation_placeholders=placeholders,
        )
        self.retry_after = retry_after


class GoveeDeviceError(GoveeException):

    translation_key = "device_error"

    def __init__(self, device_id: str, device_name: str | None = None) -> None:
        super().__init__(
            translation_key=self.translation_key,
            translation_placeholders={
                "device_id": device_id,
                "device_name": device_name or device_id,
            },
        )
        self.device_id = device_id


class GoveeCapabilityError(GoveeException):

    translation_key = "capability_not_supported"

    def __init__(self, device_id: str, capability: str) -> None:
        super().__init__(
            translation_key=self.translation_key,
            translation_placeholders={
                "device_id": device_id,
                "capability": capability,
            },
        )
        self.device_id = device_id
        self.capability = capability
