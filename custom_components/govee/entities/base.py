"""Base entity for Govee integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..coordinator import GoveeCoordinator
from ..models import GoveeDevice, GoveeDeviceState

DOMAIN = "govee"


class GoveeEntity(CoordinatorEntity[GoveeCoordinator]):
    """Base entity for Govee devices.

    Provides common functionality:
    - Device registry integration
    - Coordinator state access
    - Availability based on online status
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.device_id

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
        """Return True if entity is available.

        Group devices are always considered available for control
        since their state queries fail but control works.
        """
        if not super().available:
            return False

        # Group devices always available for control
        if self._device.is_group:
            return True

        state = self.device_state
        return state is not None and state.online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {
            "device_id": self._device_id,
            "model": self._device.sku,
        }

        if self._device.is_group:
            attrs["group_device"] = True
            attrs["assumed_state_reason"] = "Group devices cannot be queried for state"

        if self.coordinator.iot_connected:
            attrs["update_mode"] = "real-time (AWS IoT)"
        else:
            attrs["update_mode"] = "polling"

        return attrs
