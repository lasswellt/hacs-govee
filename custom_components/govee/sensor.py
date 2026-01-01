from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entities.sensor import GoveeRateLimitSensor
from .entity_descriptions.sensor import SENSOR_DESCRIPTIONS
from .models import GoveeRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[GoveeRuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator

    entities: list[GoveeRateLimitSensor] = []

    for description in SENSOR_DESCRIPTIONS.values():
        entities.append(GoveeRateLimitSensor(coordinator, description))

    _LOGGER.debug("Setting up %d Govee sensor entities", len(entities))
    async_add_entities(entities)
