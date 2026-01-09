"""Govee device model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

UNSUPPORTED_SKUS = {"SameModeGroup", "BaseGroup", "DreamViewScenic"}


@dataclass
class GoveeDevice:
    """Govee device metadata from API."""

    device_id: str
    sku: str
    device_name: str
    device_type: str
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    firmware_version: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> GoveeDevice:
        """Create device from API response."""
        return cls(
            device_id=data.get("device", ""),
            sku=data.get("sku", ""),
            device_name=data.get("deviceName", data.get("device", "Unknown")),
            device_type=data.get("type", ""),
            capabilities=data.get("capabilities", []),
            firmware_version=data.get("version"),
        )

    @property
    def is_supported(self) -> bool:
        """Check if device is supported."""
        return self.sku not in UNSUPPORTED_SKUS

    @property
    def is_group(self) -> bool:
        """Check if device is a group (can't be polled for state)."""
        return self.sku in UNSUPPORTED_SKUS

    @property
    def is_light(self) -> bool:
        """Check if device is a light."""
        return self.device_type == "devices.types.light"

    def has_capability(self, instance: str) -> bool:
        """Check if device has a capability by instance name."""
        return any(c.get("instance") == instance for c in self.capabilities)

    def get_capability(self, instance: str) -> dict[str, Any] | None:
        """Get capability by instance name."""
        for cap in self.capabilities:
            if cap.get("instance") == instance:
                return cap
        return None

    @property
    def supports_brightness(self) -> bool:
        """Check if device supports brightness control."""
        return self.has_capability("brightness")

    @property
    def supports_color(self) -> bool:
        """Check if device supports RGB color."""
        return self.has_capability("colorRgb")

    @property
    def supports_color_temp(self) -> bool:
        """Check if device supports color temperature."""
        return self.has_capability("colorTemperatureK")

    @property
    def supports_segments(self) -> bool:
        """Check if device supports segment control."""
        return self.has_capability("segmentedColorRgb")

    @property
    def supports_scenes(self) -> bool:
        """Check if device supports scenes."""
        return self.has_capability("lightScene")

    @property
    def segment_count(self) -> int:
        """Get number of segments if segmented device."""
        cap = self.get_capability("segmentedColorRgb")
        if not cap:
            return 0

        fields = cap.get("parameters", {}).get("fields", [])
        for f in fields:
            if f.get("fieldName") == "segment":
                elem_range = f.get("elementRange", {})
                return elem_range.get("max", 0) + 1
        return 0

    def get_brightness_range(self) -> tuple[int, int]:
        """Get brightness range (min, max)."""
        cap = self.get_capability("brightness")
        if cap:
            params = cap.get("parameters", {})
            range_info = params.get("range", {})
            return (range_info.get("min", 0), range_info.get("max", 100))
        return (0, 100)

    def get_color_temp_range(self) -> tuple[int, int]:
        """Get color temperature range in Kelvin (min, max)."""
        cap = self.get_capability("colorTemperatureK")
        if cap:
            params = cap.get("parameters", {})
            range_info = params.get("range", {})
            return (range_info.get("min", 2000), range_info.get("max", 9000))
        return (2000, 9000)

    def get_scene_options(self) -> list[dict[str, Any]]:
        """Get available scene options."""
        cap = self.get_capability("lightScene")
        if cap:
            return cap.get("parameters", {}).get("options", [])
        return []
