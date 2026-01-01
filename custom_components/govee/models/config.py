from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..api import GoveeApiClient
    from ..coordinator import GoveeDataUpdateCoordinator
    from .device import GoveeDevice


@dataclass
class GoveeRuntimeData:
    client: GoveeApiClient
    coordinator: GoveeDataUpdateCoordinator
    devices: dict[str, GoveeDevice]


# Type alias for ConfigEntry with GoveeRuntimeData
type GoveeConfigEntry = ConfigEntry[GoveeRuntimeData]
