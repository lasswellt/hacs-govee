"""Govee device state model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoveeDeviceState:
    """Device state from API polling or AWS IoT MQTT."""

    device_id: str
    online: bool = True
    power_state: bool | None = None
    brightness: int | None = None  # 0-100
    color_rgb: tuple[int, int, int] | None = None
    color_temp_kelvin: int | None = None

    # Segment state (optimistic only - API never returns this)
    segment_colors: dict[int, tuple[int, int, int]] = field(default_factory=dict)
    segment_brightness: dict[int, int] = field(default_factory=dict)

    # Scene state (optimistic only - API never returns active scene)
    active_scene: str | None = None
    active_scene_name: str | None = None

    @classmethod
    def from_api(cls, device_id: str, payload: dict[str, Any]) -> GoveeDeviceState:
        """Create state from API response."""
        state = cls(device_id=device_id)

        for cap in payload.get("capabilities", []):
            instance = cap.get("instance", "")
            value = cap.get("state", {}).get("value")

            if value is None:
                continue

            if instance == "powerSwitch":
                state.power_state = value == 1
            elif instance == "brightness":
                state.brightness = int(value)
            elif instance == "colorRgb":
                state.color_rgb = cls._parse_rgb(value)
            elif instance == "colorTemperatureK":
                state.color_temp_kelvin = int(value)
            elif instance == "online":
                state.online = value == 1 or value is True

        return state

    @staticmethod
    def _parse_rgb(value: int | dict[str, Any]) -> tuple[int, int, int]:
        """Parse RGB from API format."""
        if isinstance(value, dict):
            return (value.get("r", 0), value.get("g", 0), value.get("b", 0))
        # Integer format: 0xRRGGBB
        return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

    def apply_iot_state(self, iot_state: dict[str, Any]) -> None:
        """Apply state update from AWS IoT MQTT.

        AWS IoT state format:
        {"onOff": 1, "brightness": 50, "color": {"r": 255, "g": 0, "b": 0}, "colorTemInKelvin": 0}
        """
        if "onOff" in iot_state:
            self.power_state = iot_state["onOff"] == 1

        if "brightness" in iot_state:
            self.brightness = int(iot_state["brightness"])

        if "color" in iot_state:
            color = iot_state["color"]
            if isinstance(color, dict):
                self.color_rgb = (color.get("r", 0), color.get("g", 0), color.get("b", 0))
            elif isinstance(color, int):
                self.color_rgb = self._parse_rgb(color)

        if "colorTemInKelvin" in iot_state:
            temp = iot_state["colorTemInKelvin"]
            if temp > 0:  # 0 means RGB mode, not color temp
                self.color_temp_kelvin = int(temp)

    def set_segment_color(self, segment: int, rgb: tuple[int, int, int]) -> None:
        """Set optimistic segment color (API never returns this)."""
        self.segment_colors[segment] = rgb

    def set_segment_brightness(self, segment: int, brightness: int) -> None:
        """Set optimistic segment brightness (API never returns this)."""
        self.segment_brightness[segment] = brightness

    def clear_segments(self) -> None:
        """Clear segment state when main light color changes."""
        self.segment_colors.clear()
        self.segment_brightness.clear()

    def set_scene(self, scene_id: str, scene_name: str | None = None) -> None:
        """Set optimistic scene state (API never returns active scene)."""
        self.active_scene = scene_id
        self.active_scene_name = scene_name

    def clear_scene(self) -> None:
        """Clear scene state when color/brightness manually changed."""
        self.active_scene = None
        self.active_scene_name = None
