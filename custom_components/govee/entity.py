"""Base entity class for Govee integration.

Provides common functionality for all Govee entities:
- Device info
- Coordinator integration
- State updates
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import GoveeCoordinator
    from .models import GoveeDevice, GoveeDeviceState


class GoveeEntity(CoordinatorEntity["GoveeCoordinator"]):
    """Base class for Govee entities.

    Provides:
    - Automatic coordinator integration
    - Device info with rich metadata
    - Availability tracking
    - has_entity_name = True for Gold tier compliance
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoveeCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Govee data coordinator.
            device: Device this entity represents.
        """
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.device_id

        # Set unique_id based on device
        self._attr_unique_id = f"{device.device_id}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            name=self._device.name,
            manufacturer="Govee",
            model=self._device.sku,
            # Suggested area from device name (e.g., "Living Room Lamp" -> "Living Room")
            suggested_area=self._infer_area_from_name(self._device.name),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        Group devices are always considered available since we can't
        query their state but can still control them.
        """
        if self._device.is_group:
            return True

        state = self.coordinator.get_state(self._device_id)
        return state is not None and state.online

    @property
    def device_state(self) -> GoveeDeviceState | None:
        """Get current device state from coordinator."""
        return self.coordinator.get_state(self._device_id)

    @staticmethod
    def _infer_area_from_name(name: str) -> str | None:
        """Infer area from device name.

        Extracts common room names from device names like:
        - "Living Room Lamp" -> "Living Room"
        - "Bedroom LED Strip" -> "Bedroom"
        - "Kitchen Lights" -> "Kitchen"

        Returns None if no area can be inferred.
        """
        # Common area keywords (check in order)
        areas = [
            "Living Room",
            "Bedroom",
            "Kitchen",
            "Bathroom",
            "Office",
            "Dining Room",
            "Garage",
            "Basement",
            "Attic",
            "Hallway",
            "Patio",
            "Backyard",
            "Front Yard",
            "Game Room",
            "Media Room",
            "Nursery",
            "Guest Room",
            "Master Bedroom",
            "Kids Room",
        ]

        name_lower = name.lower()
        for area in areas:
            if area.lower() in name_lower:
                return area

        return None
