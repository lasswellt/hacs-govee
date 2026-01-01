from __future__ import annotations

from typing import Any, TypedDict

from .types import CapabilityCommandDict


class DeviceIdentifier(TypedDict):
    sku: str
    device: str


class DeviceStateRequestPayload(TypedDict):
    # POST /device/state
    requestId: str
    payload: DeviceIdentifier


class ControlRequestInnerPayload(TypedDict):
    sku: str
    device: str
    capability: CapabilityCommandDict


class ControlRequestPayload(TypedDict):
    # POST /device/control
    requestId: str
    payload: ControlRequestInnerPayload


class SceneRequestPayload(TypedDict):
    # POST /device/scenes or POST /device/diy-scenes
    requestId: str
    payload: DeviceIdentifier


class SceneValue(TypedDict):
    id: Any
    name: str | None


class SegmentColorValue(TypedDict):
    segment: list[int]
    rgb: int


class SegmentBrightnessValue(TypedDict):
    segment: list[int]
    brightness: int


class MusicModeValue(TypedDict):
    musicMode: str
    sensitivity: int
    autoColor: int
    color: int | None
