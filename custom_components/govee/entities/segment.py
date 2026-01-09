"""Govee segment light entity with optimistic state.

Segment state is NEVER returned by the Govee API (validated via live testing).
This entity uses fully optimistic state with RestoreEntity for persistence.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.helpers.restore_state import RestoreEntity

from ..coordinator import GoveeCoordinator
from ..models import GoveeDevice
from .base import DOMAIN, GoveeEntity

_LOGGER = logging.getLogger(__name__)


class GoveeSegmentLight(GoveeEntity, LightEntity, RestoreEntity):
    """Segment light with optimistic state.

    API never returns segment state, so this entity:
    - Uses optimistic state tracking
    - Persists state across restarts via RestoreEntity
    - Shows assumed_state = True in UI
    """

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_assumed_state = True  # Critical: Tell HA this is assumed

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
        segment_index: int,
    ) -> None:
        super().__init__(coordinator, device)

        self._segment_index = segment_index
        self._attr_unique_id = f"{device.device_id}_segment_{segment_index}"
        self._attr_name = f"Segment {segment_index + 1}"

        # Optimistic state (API never returns this)
        self._is_on: bool = False
        self._brightness: int = 255  # HA scale 0-255
        self._rgb_color: tuple[int, int, int] = (255, 255, 255)

    async def async_added_to_hass(self) -> None:
        """Restore state when added to hass."""
        await super().async_added_to_hass()

        if (last_state := await self.async_get_last_state()) is not None:
            self._is_on = last_state.state == "on"

            if (brightness := last_state.attributes.get(ATTR_BRIGHTNESS)) is not None:
                self._brightness = int(brightness)

            if (rgb := last_state.attributes.get(ATTR_RGB_COLOR)) is not None:
                self._rgb_color = tuple(rgb)  # type: ignore[arg-type]

            _LOGGER.debug(
                "Restored segment %d state: on=%s, brightness=%s, rgb=%s",
                self._segment_index,
                self._is_on,
                self._brightness,
                self._rgb_color,
            )

    @property
    def is_on(self) -> bool:
        """Return true if segment is on."""
        return self._is_on

    @property
    def brightness(self) -> int:
        """Return brightness (0-255)."""
        return self._brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return RGB color."""
        return self._rgb_color

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the segment.

        Sets segment color via API and updates optimistic state.
        """
        # Determine target RGB color
        if ATTR_RGB_COLOR in kwargs:
            target_rgb = kwargs[ATTR_RGB_COLOR]
        elif self._rgb_color != (0, 0, 0):
            target_rgb = self._rgb_color
        else:
            target_rgb = (255, 255, 255)  # Default to white

        # Send color command to API
        await self.coordinator.async_set_segment_color(
            self._device_id,
            self._segment_index,
            target_rgb,
        )

        # Update optimistic state
        self._is_on = True
        self._rgb_color = target_rgb

        # Handle brightness if provided
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            # Convert HA 0-255 to API 0-100 (use round to avoid truncation errors)
            api_brightness = round(brightness * 100 / 255)
            await self.coordinator.async_set_segment_brightness(
                self._device_id,
                self._segment_index,
                api_brightness,
            )
            self._brightness = brightness

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the segment by setting to black."""
        # Skip if already off
        if not self._is_on and self._rgb_color == (0, 0, 0):
            _LOGGER.debug("Segment %d already off, skipping", self._segment_index)
            return

        await self.coordinator.async_set_segment_color(
            self._device_id,
            self._segment_index,
            (0, 0, 0),
        )

        self._is_on = False
        self._rgb_color = (0, 0, 0)
        self.async_write_ha_state()
