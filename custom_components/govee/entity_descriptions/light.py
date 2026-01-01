from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.light import LightEntityDescription


@dataclass(frozen=True, kw_only=True)
class GoveeLightEntityDescription(LightEntityDescription):
    """Describes a Govee light entity."""


@dataclass(frozen=True, kw_only=True)
class GoveeSegmentLightDescription(GoveeLightEntityDescription):
    """Describes a Govee segment light entity.

    Used for individual RGBIC device segments.
    Segments are automatically created and enabled for RGBIC devices.
    Users can disable individual segments via the entity registry if desired.
    """

    key: str = "segment"
    translation_key: str = "segment"
    entity_registry_enabled_default: bool = True


LIGHT_DESCRIPTIONS: dict[str, GoveeLightEntityDescription] = {
    "main": GoveeLightEntityDescription(
        key="main",
        entity_registry_enabled_default=True,
    ),
}

SEGMENT_LIGHT_DESCRIPTION = GoveeSegmentLightDescription()
