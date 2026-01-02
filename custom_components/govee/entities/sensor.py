"""Sensor entities for Govee integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from ..coordinator import GoveeDataUpdateCoordinator
from ..entity_descriptions.sensor import GoveeSensorEntityDescription


class GoveeRateLimitSensor(SensorEntity):
    """Integration-level sensor (not device-specific) for monitoring API rate limits."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoveeDataUpdateCoordinator,
        description: GoveeSensorEntityDescription,
    ) -> None:
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"govee_{description.key}"
        self._attr_device_info = None

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def native_value(self) -> int | None:
        if self.entity_description.key == "rate_limit_remaining_minute":
            return self._coordinator.rate_limit_remaining_minute
        elif self.entity_description.key == "rate_limit_remaining_day":
            return self._coordinator.rate_limit_remaining
        return None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
