from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonDeviceClass, ButtonEntityDescription
from homeassistant.const import EntityCategory


@dataclass(frozen=True, kw_only=True)
class GoveeButtonEntityDescription(ButtonEntityDescription):
    """Describes a Govee button entity."""


BUTTON_DESCRIPTIONS: dict[str, GoveeButtonEntityDescription] = {
    "refresh_scenes": GoveeButtonEntityDescription(
        key="refresh_scenes",
        translation_key="refresh_scenes",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:refresh",
    ),
    "identify": GoveeButtonEntityDescription(
        key="identify",
        translation_key="identify",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=ButtonDeviceClass.IDENTIFY,
        icon="mdi:lightbulb-alert",
    ),
}
