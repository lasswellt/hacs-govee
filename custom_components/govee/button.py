from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_LIGHT
from .entities.button import GoveeIdentifyButton, GoveeRefreshScenesButton
from .entity_descriptions.button import BUTTON_DESCRIPTIONS
from .models import GoveeRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[GoveeRuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    devices = entry.runtime_data.devices

    entities: list[GoveeRefreshScenesButton | GoveeIdentifyButton] = []

    for device in devices.values():
        entities.append(
            GoveeIdentifyButton(
                coordinator,
                device,
                BUTTON_DESCRIPTIONS["identify"],
            )
        )

        if device.device_type == DEVICE_TYPE_LIGHT:
            entities.append(
                GoveeRefreshScenesButton(
                    coordinator,
                    device,
                    BUTTON_DESCRIPTIONS["refresh_scenes"],
                )
            )

    _LOGGER.debug("Setting up %d Govee button entities", len(entities))
    async_add_entities(entities)
