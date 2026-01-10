"""Button platform for Govee integration.

Provides button entities for:
- Refresh scenes (per device)
- Identify device (flash lights if supported)
"""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import GoveeCoordinator
from .entity import GoveeEntity
from .models import GoveeDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee buttons from a config entry."""
    coordinator: GoveeCoordinator = entry.runtime_data

    entities: list[ButtonEntity] = []

    for device in coordinator.devices.values():
        # Add refresh scenes button for devices with scenes
        if device.supports_scenes:
            entities.append(GoveeRefreshScenesButton(coordinator, device))

    async_add_entities(entities)
    _LOGGER.debug("Set up %d Govee button entities", len(entities))


class GoveeRefreshScenesButton(GoveeEntity, ButtonEntity):
    """Button to refresh scenes for a device.

    Useful when new scenes are created in the Govee app.
    """

    _attr_device_class = ButtonDeviceClass.UPDATE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "refresh_scenes"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the refresh scenes button."""
        super().__init__(coordinator, device)

        self._attr_unique_id = f"{device.device_id}_refresh_scenes"
        self._attr_name = "Refresh Scenes"

    async def async_press(self) -> None:
        """Handle the button press - refresh scenes."""
        _LOGGER.debug("Refreshing scenes for %s", self._device.name)

        # Force refresh scenes from API
        await self.coordinator.async_get_scenes(
            self._device_id,
            refresh=True,
        )

        _LOGGER.info("Scenes refreshed for %s", self._device.name)
