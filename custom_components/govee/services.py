from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_SEGMENT_COLOR = "set_segment_color"
SERVICE_SET_SEGMENT_BRIGHTNESS = "set_segment_brightness"
SERVICE_SET_MUSIC_MODE = "set_music_mode"
SERVICE_REFRESH_SCENES = "refresh_scenes"


async def async_setup_services(hass: HomeAssistant) -> None:
    _LOGGER.debug("Setting up Govee services")

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_SEGMENT_COLOR,
        {
            vol.Required("segments"): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Required("rgb_color"): vol.All(
                vol.Coerce(tuple),
                vol.ExactSequence([cv.byte, cv.byte, cv.byte]),
            ),
        },
        "async_set_segment_color",
    )

    platform.async_register_entity_service(
        SERVICE_SET_SEGMENT_BRIGHTNESS,
        {
            vol.Required("segments"): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Required("brightness"): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
        },
        "async_set_segment_brightness",
    )

    platform.async_register_entity_service(
        SERVICE_SET_MUSIC_MODE,
        {
            vol.Required("mode"): cv.string,
            vol.Optional("sensitivity", default=50): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional("auto_color", default=True): cv.boolean,
            vol.Optional("rgb_color"): vol.All(
                vol.Coerce(tuple),
                vol.ExactSequence([cv.byte, cv.byte, cv.byte]),
            ),
        },
        "async_set_music_mode",
    )


async def async_setup_select_services(hass: HomeAssistant) -> None:
    _LOGGER.debug("Setting up Govee select services")

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_REFRESH_SCENES,
        {},
        "async_refresh_scenes",
    )
