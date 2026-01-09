"""Govee models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .device import GoveeDevice
from .state import GoveeDeviceState

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..api.client import GoveeApiClient
    from ..coordinator import GoveeCoordinator


@dataclass
class GoveeRuntimeData:
    """Runtime data for Govee integration."""

    client: GoveeApiClient
    coordinator: GoveeCoordinator
    devices: dict[str, GoveeDevice]


type GoveeConfigEntry = ConfigEntry[GoveeRuntimeData]


__all__ = [
    "GoveeDevice",
    "GoveeDeviceState",
    "GoveeRuntimeData",
    "GoveeConfigEntry",
]
