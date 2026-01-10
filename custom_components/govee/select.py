"""Select platform for Govee integration.

Provides select entities for scene control - one dropdown per device.
This replaces individual scene entities with a more manageable interface.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENABLE_SCENES, DEFAULT_ENABLE_SCENES, DOMAIN
from .coordinator import GoveeCoordinator
from .models import GoveeDevice, SceneCommand

_LOGGER = logging.getLogger(__name__)

# Option for "no scene" / off state
SCENE_NONE = "None"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee scene selects from a config entry."""
    coordinator: GoveeCoordinator = entry.runtime_data

    # Check if scenes are enabled
    if not entry.options.get(CONF_ENABLE_SCENES, DEFAULT_ENABLE_SCENES):
        _LOGGER.debug("Scene select entities disabled")
        return

    entities: list[SelectEntity] = []

    for device in coordinator.devices.values():
        if device.supports_scenes:
            # Fetch scenes for this device
            scenes = await coordinator.async_get_scenes(device.device_id)

            if scenes:
                entities.append(
                    GoveeSceneSelectEntity(
                        coordinator=coordinator,
                        device=device,
                        scenes=scenes,
                    )
                )

    async_add_entities(entities)
    _LOGGER.debug("Set up %d Govee scene select entities", len(entities))


class GoveeSceneSelectEntity(CoordinatorEntity["GoveeCoordinator"], SelectEntity):
    """Govee scene select entity.

    Provides a dropdown to select and activate scenes on a device.
    Much more manageable than individual scene entities.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "govee_scene_select"
    _attr_icon = "mdi:palette"

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
        scenes: list[dict[str, Any]],
    ) -> None:
        """Initialize the scene select entity.

        Args:
            coordinator: Govee data coordinator.
            device: Device this select belongs to.
            scenes: List of scene data from API.
        """
        super().__init__(coordinator)

        self._device = device
        self._device_id = device.device_id

        # Build scene mapping: name -> (id, name)
        self._scene_map: dict[str, tuple[int, str]] = {}
        options = [SCENE_NONE]

        for scene_data in scenes:
            scene_id = scene_data.get("value", {}).get("id", 0)
            scene_name = scene_data.get("name", f"Scene {scene_id}")

            # Handle duplicate names by appending ID
            unique_name = scene_name
            counter = 1
            while unique_name in self._scene_map:
                unique_name = f"{scene_name} ({counter})"
                counter += 1

            self._scene_map[unique_name] = (scene_id, scene_name)
            options.append(unique_name)

        self._attr_options = options
        self._attr_current_option = SCENE_NONE

        # Unique ID
        self._attr_unique_id = f"{device.device_id}_scene_select"

        # Entity name
        self._attr_name = "Scene"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            name=self._device.name,
            manufacturer="Govee",
            model=self._device.sku,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        state = self.coordinator.get_state(self._device_id)
        if state is None:
            return False
        return state.online or self._device.is_group

    async def async_select_option(self, option: str) -> None:
        """Handle scene selection."""
        if option == SCENE_NONE:
            # Just update state, don't send command
            self._attr_current_option = SCENE_NONE
            self.async_write_ha_state()
            return

        scene_info = self._scene_map.get(option)
        if not scene_info:
            _LOGGER.warning("Unknown scene option: %s", option)
            return

        scene_id, scene_name = scene_info

        command = SceneCommand(
            scene_id=scene_id,
            scene_name=scene_name,
        )

        success = await self.coordinator.async_control_device(
            self._device_id,
            command,
        )

        if success:
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.debug(
                "Activated scene '%s' on %s",
                scene_name,
                self._device.name,
            )
        else:
            _LOGGER.warning(
                "Failed to activate scene '%s' on %s",
                scene_name,
                self._device.name,
            )
