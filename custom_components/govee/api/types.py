from __future__ import annotations

from typing import Any, TypedDict

from typing_extensions import NotRequired


class RangeDict(TypedDict):
    min: int
    max: int
    precision: NotRequired[int]


class OptionDict(TypedDict):
    name: str
    value: Any


class FieldDict(TypedDict):
    fieldName: str
    type: str
    elementRange: NotRequired[RangeDict]


class ParametersDict(TypedDict):
    # dataType can be "INTEGER", "ENUM", "STRUCT", etc.
    dataType: str
    range: NotRequired[RangeDict]
    options: NotRequired[list[OptionDict]]
    fields: NotRequired[list[FieldDict]]


class CapabilityStateDict(TypedDict):
    value: Any


class StateCapabilityDict(TypedDict):
    type: str
    instance: str
    state: CapabilityStateDict


class DeviceCapabilityDict(TypedDict):
    type: str
    instance: str
    parameters: NotRequired[ParametersDict]


class SceneOptionDict(TypedDict):
    name: str
    value: Any
    category: NotRequired[str]


class CapabilityCommandDict(TypedDict):
    type: str
    instance: str
    value: Any
