"""Switch platform for Govee integration.

Provides switch entities for:
- Smart plugs (on/off control)
- Night light toggle (for lights with night light mode)
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import GoveeCoordinator
from .entity import GoveeEntity
from .models import GoveeDevice, PowerCommand, create_night_light_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee switches from a config entry."""
    coordinator: GoveeCoordinator = entry.runtime_data

    entities: list[SwitchEntity] = []

    for device in coordinator.devices.values():
        # Create switch for smart plugs (power on/off)
        if device.is_plug and device.supports_power:
            entities.append(GoveePlugSwitchEntity(coordinator, device))

        # Create switch for night light toggle (lights with night light mode)
        if device.supports_night_light:
            entities.append(GoveeNightLightSwitchEntity(coordinator, device))

    async_add_entities(entities)
    _LOGGER.debug("Set up %d Govee switch entities", len(entities))


class GoveePlugSwitchEntity(GoveeEntity, SwitchEntity):
    """Govee smart plug switch entity.

    Controls power state for Govee smart plugs.
    """

    _attr_device_class = SwitchDeviceClass.OUTLET
    _attr_translation_key = "govee_plug"

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the plug switch entity."""
        super().__init__(coordinator, device)

        # Use device name as entity name
        self._attr_name = None

    @property
    def is_on(self) -> bool | None:
        """Return True if plug is on."""
        state = self.device_state
        return state.power_state if state else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the plug on."""
        await self.coordinator.async_control_device(
            self._device_id,
            PowerCommand(power_on=True),
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the plug off."""
        await self.coordinator.async_control_device(
            self._device_id,
            PowerCommand(power_on=False),
        )


class GoveeNightLightSwitchEntity(GoveeEntity, SwitchEntity):
    """Govee night light toggle switch entity.

    Controls night light mode for devices that support it.
    Uses optimistic state since API may not return night light status.
    """

    _attr_translation_key = "govee_night_light"

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the night light switch entity."""
        super().__init__(coordinator, device)

        # Unique ID for night light switch
        self._attr_unique_id = f"{device.device_id}_night_light"

        # Name as "Night Light"
        self._attr_name = "Night Light"

        # Optimistic state
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return True if night light is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn night light on."""
        success = await self.coordinator.async_control_device(
            self._device_id,
            create_night_light_command(enabled=True),
        )
        if success:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn night light off."""
        success = await self.coordinator.async_control_device(
            self._device_id,
            create_night_light_command(enabled=False),
        )
        if success:
            self._is_on = False
            self.async_write_ha_state()
