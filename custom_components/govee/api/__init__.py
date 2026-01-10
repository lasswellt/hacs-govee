"""API layer for Govee integration.

Contains REST client, MQTT client, and authentication.
"""

from .auth import GoveeAuthClient, GoveeIotCredentials, validate_govee_credentials
from .client import GoveeApiClient
from .exceptions import (
    GoveeApiError,
    GoveeAuthError,
    GoveeConnectionError,
    GoveeDeviceNotFoundError,
    GoveeRateLimitError,
)
from .mqtt import GoveeAwsIotClient

__all__ = [
    # Client
    "GoveeApiClient",
    # Auth
    "GoveeAuthClient",
    "GoveeIotCredentials",
    "validate_govee_credentials",
    # MQTT
    "GoveeAwsIotClient",
    # Exceptions
    "GoveeApiError",
    "GoveeAuthError",
    "GoveeConnectionError",
    "GoveeDeviceNotFoundError",
    "GoveeRateLimitError",
]
