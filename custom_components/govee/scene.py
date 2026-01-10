"""Scene platform for Govee integration.

Provides dedicated scene entities for each Govee device scene.
Scenes are discoverable and can be activated via automations.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLE_SCENES, DEFAULT_ENABLE_SCENES, DOMAIN
from .coordinator import GoveeCoordinator
from .models import GoveeDevice, SceneCommand

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee scenes from a config entry."""
    coordinator: GoveeCoordinator = entry.runtime_data

    # Check if scenes are enabled
    if not entry.options.get(CONF_ENABLE_SCENES, DEFAULT_ENABLE_SCENES):
        _LOGGER.debug("Scene entities disabled")
        return

    entities: list[Scene] = []

    for device in coordinator.devices.values():
        if device.supports_scenes:
            # Fetch scenes for this device
            scenes = await coordinator.async_get_scenes(device.device_id)

            for scene_data in scenes:
                entities.append(
                    GoveeSceneEntity(
                        coordinator=coordinator,
                        device=device,
                        scene_id=scene_data.get("value", {}).get("id", 0),
                        scene_name=scene_data.get("name", "Unknown"),
                    )
                )

    async_add_entities(entities)
    _LOGGER.debug("Set up %d Govee scene entities", len(entities))


class GoveeSceneEntity(Scene):
    """Govee scene entity.

    Represents a single scene that can be activated on a device.
    Scenes are lazy-loaded and cached to minimize API calls.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "govee_scene"

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
        scene_id: int,
        scene_name: str,
    ) -> None:
        """Initialize the scene entity.

        Args:
            coordinator: Govee data coordinator.
            device: Device this scene belongs to.
            scene_id: Scene ID from Govee API.
            scene_name: Scene name from Govee API.
        """
        self._coordinator = coordinator
        self._device = device
        self._device_id = device.device_id
        self._scene_id = scene_id
        self._scene_name = scene_name

        # Unique ID combines device and scene
        self._attr_unique_id = f"{device.device_id}_scene_{scene_id}"

        # Use scene name as entity name
        self._attr_name = scene_name

        # Translation placeholders
        self._attr_translation_placeholders = {"scene_name": scene_name}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            name=self._device.name,
            manufacturer="Govee",
            model=self._device.sku,
        )

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        command = SceneCommand(
            scene_id=self._scene_id,
            scene_name=self._scene_name,
        )

        success = await self._coordinator.async_control_device(
            self._device_id,
            command,
        )

        if success:
            _LOGGER.debug(
                "Activated scene '%s' on %s",
                self._scene_name,
                self._device.name,
            )
        else:
            _LOGGER.warning(
                "Failed to activate scene '%s' on %s",
                self._scene_name,
                self._device.name,
            )
