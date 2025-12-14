"""Govee switch platform for smart plugs, sockets, and feature toggles."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GoveeConfigEntry
from .api.const import (
    CAPABILITY_ON_OFF,
    CAPABILITY_TOGGLE,
    INSTANCE_NIGHTLIGHT_TOGGLE,
    INSTANCE_POWER_SWITCH,
)
from .const import DEVICE_TYPE_LIGHT, DEVICE_TYPE_SOCKET
from .coordinator import GoveeDataUpdateCoordinator
from .entity import GoveeEntity
from .models import GoveeDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoveeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee switches from a config entry."""
    coordinator = entry.runtime_data.coordinator
    devices = entry.runtime_data.devices

    entities: list[SwitchEntity] = []

    for device in devices.values():
        # Create switch entities for socket/plug devices
        if device.device_type == DEVICE_TYPE_SOCKET:
            entities.append(GoveeSwitchEntity(coordinator, device))

        # Create nightlight switch for light devices that support it
        if device.device_type == DEVICE_TYPE_LIGHT and device.supports_nightlight:
            entities.append(GoveeNightLightSwitch(coordinator, device))

    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities)


class GoveeSwitchEntity(GoveeEntity, SwitchEntity):
    """Govee smart plug/socket entity."""

    _attr_device_class = SwitchDeviceClass.OUTLET
    _attr_name = None  # Use device name

    def __init__(
        self,
        coordinator: GoveeDataUpdateCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"govee_{device.device_id}_switch"

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        state = self.device_state
        if state is None:
            return None
        return state.power_state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on %s", self._device.device_name)
        try:
            await self.coordinator.async_control_device(
                self._device_id,
                CAPABILITY_ON_OFF,
                INSTANCE_POWER_SWITCH,
                1,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn on %s: %s",
                self._device.device_name,
                err,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off %s", self._device.device_name)
        try:
            await self.coordinator.async_control_device(
                self._device_id,
                CAPABILITY_ON_OFF,
                INSTANCE_POWER_SWITCH,
                0,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off %s: %s",
                self._device.device_name,
                err,
            )


class GoveeNightLightSwitch(GoveeEntity, SwitchEntity):
    """Govee night light toggle switch entity."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "nightlight"

    def __init__(
        self,
        coordinator: GoveeDataUpdateCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the nightlight switch entity."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"govee_{device.device_id}_nightlight"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._device.device_name} Night Light"

    @property
    def is_on(self) -> bool | None:
        """Return true if nightlight is on."""
        state = self.device_state
        if state is None:
            return None
        return state.nightlight_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the nightlight on."""
        _LOGGER.debug("Turning on nightlight for %s", self._device.device_name)
        try:
            await self.coordinator.async_control_device(
                self._device_id,
                CAPABILITY_TOGGLE,
                INSTANCE_NIGHTLIGHT_TOGGLE,
                1,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn on nightlight for %s: %s",
                self._device.device_name,
                err,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the nightlight off."""
        _LOGGER.debug("Turning off nightlight for %s", self._device.device_name)
        try:
            await self.coordinator.async_control_device(
                self._device_id,
                CAPABILITY_TOGGLE,
                INSTANCE_NIGHTLIGHT_TOGGLE,
                0,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off nightlight for %s: %s",
                self._device.device_name,
                err,
            )
