"""Light platform for Govee integration."""
from __future__ import annotations

import logging

from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .models import GoveeConfigEntry
from .entities import GoveeLightEntity, GoveeSegmentLight

_LOGGER = logging.getLogger(__name__)

MAX_SEGMENTS_WARNING = 20


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoveeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee light entities."""
    coordinator = entry.runtime_data.coordinator
    devices = entry.runtime_data.devices

    entities: list[LightEntity] = []
    segment_count_total = 0

    for device in devices.values():
        # Add main light entity for all light-type devices
        if device.is_light:
            entities.append(GoveeLightEntity(coordinator, device))

            # Add segment entities if device supports segments
            if device.supports_segments:
                segment_count = device.segment_count

                if segment_count > MAX_SEGMENTS_WARNING:
                    _LOGGER.warning(
                        "Device %s (%s) reports %d segments - unusually high",
                        device.device_name,
                        device.sku,
                        segment_count,
                    )

                for segment_index in range(segment_count):
                    entities.append(
                        GoveeSegmentLight(coordinator, device, segment_index)
                    )

                segment_count_total += segment_count
                _LOGGER.debug(
                    "Created %d segment entities for %s",
                    segment_count,
                    device.device_name,
                )

    _LOGGER.info(
        "Adding %d light entities (%d main, %d segments)",
        len(entities),
        len(entities) - segment_count_total,
        segment_count_total,
    )

    async_add_entities(entities)
