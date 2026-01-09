"""Govee main light entity with source-based state."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)

from ..coordinator import GoveeCoordinator
from ..models import GoveeDevice
from .base import GoveeEntity

_LOGGER = logging.getLogger(__name__)

# Brightness conversion constants
HA_BRIGHTNESS_MAX = 255
API_BRIGHTNESS_MAX = 100


class GoveeLightEntity(GoveeEntity, LightEntity):
    """Govee light entity with source-based state management.

    Uses source-based state (poll after command) for main device attributes
    to avoid the "flipflop" bug from optimistic updates.

    When AWS IoT is connected, state updates arrive in real-time via MQTT push.
    When only API key is provided, state is polled after each command.
    """

    _attr_name = None  # Use device name from DeviceInfo

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = device.device_id

        # Configure supported features based on device capabilities
        self._attr_supported_color_modes = self._determine_color_modes()
        self._attr_supported_features = self._determine_features()

        # Color temperature range
        temp_range = device.get_color_temp_range()
        self._attr_min_color_temp_kelvin = temp_range[0]
        self._attr_max_color_temp_kelvin = temp_range[1]

        # Effect list from device capabilities
        self._effect_map: dict[str, dict[str, Any]] = {}
        self._build_effect_list()

    def _determine_color_modes(self) -> set[ColorMode]:
        """Determine supported color modes from device capabilities."""
        modes: set[ColorMode] = set()

        if self._device.supports_color:
            modes.add(ColorMode.RGB)
        if self._device.supports_color_temp:
            modes.add(ColorMode.COLOR_TEMP)

        if not modes:
            if self._device.supports_brightness:
                modes.add(ColorMode.BRIGHTNESS)
            else:
                modes.add(ColorMode.ONOFF)

        return modes

    def _determine_features(self) -> LightEntityFeature:
        """Determine supported features from device capabilities."""
        features = LightEntityFeature(0)

        if self._device.supports_scenes:
            features |= LightEntityFeature.EFFECT

        return features

    def _build_effect_list(self) -> None:
        """Build effect list from device scene options."""
        scene_options = self._device.get_scene_options()

        effects: list[str] = []
        for option in scene_options:
            name = option.get("name", "")
            if name:
                effects.append(name)
                self._effect_map[name] = option

        if effects:
            self._attr_effect_list = sorted(effects)

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        state = self.device_state
        if state is None:
            return None
        return state.power_state

    @property
    def brightness(self) -> int | None:
        """Return brightness (0-255)."""
        state = self.device_state
        if state is None or state.brightness is None:
            return None
        # Convert API 0-100 to HA 0-255
        return int(state.brightness * HA_BRIGHTNESS_MAX / API_BRIGHTNESS_MAX)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return RGB color."""
        state = self.device_state
        return state.color_rgb if state else None

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return color temperature in Kelvin."""
        state = self.device_state
        return state.color_temp_kelvin if state else None

    @property
    def color_mode(self) -> ColorMode | None:
        """Return current color mode."""
        state = self.device_state
        if state is None:
            return None

        supported = self._attr_supported_color_modes
        if supported is None:
            return ColorMode.ONOFF

        # Determine mode from current state
        if state.color_temp_kelvin and ColorMode.COLOR_TEMP in supported:
            return ColorMode.COLOR_TEMP
        if state.color_rgb and ColorMode.RGB in supported:
            return ColorMode.RGB
        if ColorMode.BRIGHTNESS in supported:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def effect(self) -> str | None:
        """Return current effect/scene name."""
        state = self.device_state
        return state.active_scene_name if state else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light.

        Command order: Color/ColorTemp FIRST -> Brightness LAST
        This prevents revert issues observed in govee2mqtt testing.
        """
        # Handle effect separately - mutually exclusive with other attributes
        if ATTR_EFFECT in kwargs:
            await self._async_set_effect(kwargs[ATTR_EFFECT])
            return

        # Send color/temp command first
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            color_int = (r << 16) + (g << 8) + b
            await self.coordinator.async_send_command(
                self._device_id,
                "devices.capabilities.color_setting",
                "colorRgb",
                color_int,
            )

        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            min_k = self._attr_min_color_temp_kelvin or 2000
            max_k = self._attr_max_color_temp_kelvin or 9000
            temp = max(min_k, min(max_k, temp))
            await self.coordinator.async_send_command(
                self._device_id,
                "devices.capabilities.color_setting",
                "colorTemperatureK",
                temp,
            )

        # Send brightness command (after color)
        if ATTR_BRIGHTNESS in kwargs:
            # Convert HA 0-255 to API 0-100 (use round to avoid truncation errors)
            api_brightness = round(kwargs[ATTR_BRIGHTNESS] * API_BRIGHTNESS_MAX / HA_BRIGHTNESS_MAX)
            min_b, max_b = self._device.get_brightness_range()
            api_brightness = max(min_b, min(max_b, api_brightness))
            await self.coordinator.async_send_command(
                self._device_id,
                "devices.capabilities.range",
                "brightness",
                api_brightness,
            )

        # If no attributes specified, just turn on
        if not any(k in kwargs for k in (ATTR_RGB_COLOR, ATTR_COLOR_TEMP_KELVIN, ATTR_BRIGHTNESS, ATTR_EFFECT)):
            await self.coordinator.async_send_command(
                self._device_id,
                "devices.capabilities.on_off",
                "powerSwitch",
                1,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.async_send_command(
            self._device_id,
            "devices.capabilities.on_off",
            "powerSwitch",
            0,
        )

    async def _async_set_effect(self, effect_name: str) -> None:
        """Set light effect/scene."""
        if effect_name not in self._effect_map:
            _LOGGER.warning("Unknown effect '%s' for %s", effect_name, self._device.device_name)
            return

        scene_data = self._effect_map[effect_name]
        scene_value = scene_data.get("value")

        await self.coordinator.async_set_scene(
            self._device_id,
            scene_value,
            scene_name=effect_name,
        )
