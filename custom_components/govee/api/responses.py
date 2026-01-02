from __future__ import annotations

from typing import TypedDict

from typing_extensions import NotRequired

from .types import DeviceCapabilityDict, ParametersDict, StateCapabilityDict


class DeviceDict(TypedDict):
    device: str
    sku: str
    deviceName: str
    type: str
    capabilities: list[DeviceCapabilityDict]
    version: NotRequired[str]


class DeviceStatePayload(TypedDict):
    capabilities: list[StateCapabilityDict]


class ControlResponsePayload(TypedDict):
    pass


class SceneCapabilityDict(TypedDict):
    type: str
    instance: str
    parameters: ParametersDict


class DynamicScenesPayload(TypedDict):
    capabilities: list[SceneCapabilityDict]


class DIYScenesPayload(TypedDict):
    capabilities: list[SceneCapabilityDict]


class ApiResponseBase(TypedDict):
    code: int
    message: str


class DevicesResponse(ApiResponseBase):
    # GET /devices - uses 'data' instead of 'payload'
    data: NotRequired[list[DeviceDict]]


class DeviceStateResponse(TypedDict):
    # POST /device/state
    code: int
    message: str
    payload: NotRequired[DeviceStatePayload]


class ControlResponse(TypedDict):
    # POST /device/control
    code: int
    message: str
    payload: NotRequired[ControlResponsePayload]


class DynamicScenesResponse(TypedDict):
    # POST /device/scenes
    code: int
    message: str
    payload: NotRequired[DynamicScenesPayload]


class DIYScenesResponse(TypedDict):
    # POST /device/diy-scenes
    code: int
    message: str
    payload: NotRequired[DIYScenesPayload]
