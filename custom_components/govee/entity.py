"""Base entity for Govee integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoveeDataUpdateCoordinator
from .models import GoveeDevice, GoveeDeviceState


class GoveeEntity(CoordinatorEntity[GoveeDataUpdateCoordinator]):
    """Base entity for Govee devices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoveeDataUpdateCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.device_id

        # Set up device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.device_name,
            manufacturer="Govee",
            model=device.sku,
            sw_version=device.firmware_version,
        )

    @property
    def device_state(self) -> GoveeDeviceState | None:
        """Get current device state from coordinator."""
        return self.coordinator.get_state(self._device_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False

        state = self.device_state
        if state is None:
            return False

        return state.online

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        return {
            "device_id": self._device_id,
            "model": self._device.sku,
            "rate_limit_remaining": self.coordinator.rate_limit_remaining,
            "rate_limit_remaining_minute": self.coordinator.rate_limit_remaining_minute,
        }
