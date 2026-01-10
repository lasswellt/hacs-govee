"""Domain models for Govee integration.

All models are frozen dataclasses for immutability.
"""

from .commands import (
    BrightnessCommand,
    ColorCommand,
    ColorTempCommand,
    DeviceCommand,
    PowerCommand,
    SceneCommand,
    SegmentColorCommand,
    ToggleCommand,
    create_night_light_command,
)
from .device import (
    ColorTempRange,
    GoveeCapability,
    GoveeDevice,
    SegmentCapability,
)
from .state import GoveeDeviceState, RGBColor, SegmentState

__all__ = [
    # Device
    "GoveeDevice",
    "GoveeCapability",
    "ColorTempRange",
    "SegmentCapability",
    # State
    "GoveeDeviceState",
    "RGBColor",
    "SegmentState",
    # Commands
    "DeviceCommand",
    "PowerCommand",
    "BrightnessCommand",
    "ColorCommand",
    "ColorTempCommand",
    "SceneCommand",
    "SegmentColorCommand",
    "ToggleCommand",
    "create_night_light_command",
]
