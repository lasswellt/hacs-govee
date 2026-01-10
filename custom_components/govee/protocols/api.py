"""API layer protocol interfaces.

Defines contracts for API client and authentication provider implementations.
These protocols enable dependency injection and testing with mock implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..models.commands import DeviceCommand
    from ..models.device import GoveeDevice
    from ..models.state import GoveeDeviceState


@runtime_checkable
class IApiClient(Protocol):
    """Protocol for Govee API client operations.

    Defines the contract for REST API communication with Govee cloud.
    Implementations must handle rate limiting, retries, and error mapping.
    """

    async def get_devices(self) -> list[GoveeDevice]:
        """Fetch all devices from Govee API.

        Returns:
            List of GoveeDevice instances with capabilities.

        Raises:
            GoveeAuthError: Invalid API key.
            GoveeRateLimitError: Rate limit exceeded.
            GoveeConnectionError: Network/connection error.
        """
        ...

    async def get_device_state(
        self,
        device_id: str,
        sku: str,
    ) -> GoveeDeviceState:
        """Fetch current state for a device.

        Args:
            device_id: Device identifier (MAC address format).
            sku: Device SKU/model number.

        Returns:
            GoveeDeviceState with current values.

        Raises:
            GoveeApiError: If state query fails.
        """
        ...

    async def control_device(
        self,
        device_id: str,
        sku: str,
        command: DeviceCommand,
    ) -> bool:
        """Send control command to device.

        Args:
            device_id: Device identifier.
            sku: Device SKU.
            command: Command to execute.

        Returns:
            True if command was accepted by API.

        Raises:
            GoveeApiError: If command fails.
        """
        ...

    async def get_dynamic_scenes(
        self,
        device_id: str,
        sku: str,
    ) -> list[dict[str, Any]]:
        """Fetch available scenes for a device.

        Args:
            device_id: Device identifier.
            sku: Device SKU.

        Returns:
            List of scene definitions with id, name, etc.
        """
        ...

    async def close(self) -> None:
        """Close the API client and release resources."""
        ...


@runtime_checkable
class IAuthProvider(Protocol):
    """Protocol for authentication provider.

    Handles Govee account login and IoT credential retrieval.
    Credentials are used for AWS IoT MQTT real-time updates.
    """

    async def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """Authenticate with Govee account.

        Args:
            email: Govee account email.
            password: Govee account password.

        Returns:
            Dict containing token, IoT credentials, etc.

        Raises:
            GoveeAuthError: Invalid credentials.
            GoveeApiError: API communication error.
        """
        ...

    async def get_iot_credentials(
        self,
        token: str,
    ) -> dict[str, Any]:
        """Fetch IoT credentials for MQTT connection.

        Args:
            token: Authentication token from login.

        Returns:
            Dict with certificate, key, endpoint, etc.

        Raises:
            GoveeApiError: If credential fetch fails.
        """
        ...

    async def close(self) -> None:
        """Close the auth provider and release resources."""
        ...
