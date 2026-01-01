from __future__ import annotations

import logging

from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GoveeConfigEntry
from .const import DEVICE_TYPE_LIGHT
from .entities import GoveeLightEntity
from .entities.segment import GoveeSegmentLight
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

MAX_SEGMENTS_WARNING = 20


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoveeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    devices = entry.runtime_data.devices

    entities: list[LightEntity] = []
    segment_count_total = 0

    for device in devices.values():
        if device.device_type == DEVICE_TYPE_LIGHT or device.supports_on_off:
            entities.append(GoveeLightEntity(coordinator, device, entry))

            if device.supports_segments:
                segment_count = device.get_segment_count()

                if segment_count > MAX_SEGMENTS_WARNING:
                    _LOGGER.warning(
                        "Device %s (%s) reports %d segments, which is unusually high. "
                        "Creating all segment entities anyway.",
                        device.device_name,
                        device.sku,
                        segment_count,
                    )

                for segment_index in range(segment_count):
                    entities.append(
                        GoveeSegmentLight(
                            coordinator,
                            device,
                            segment_index,
                        )
                    )

                segment_count_total += segment_count
                _LOGGER.debug(
                    "Created %d segment entities for device %s (%s)",
                    segment_count,
                    device.device_name,
                    device.sku,
                )

    _LOGGER.debug(
        "Adding %d light entities (%d main lights, %d segments)",
        len(entities),
        len(entities) - segment_count_total,
        segment_count_total,
    )
    async_add_entities(entities)

    await async_setup_services(hass)
