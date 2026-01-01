from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapabilityParameter:
    data_type: str
    range: dict[str, int] | None = None
    options: list[dict[str, Any]] | None = None
    fields: list[dict[str, Any]] | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> CapabilityParameter:
        return cls(
            data_type=data.get("dataType", ""),
            range=data.get("range"),
            options=data.get("options"),
            fields=data.get("fields"),
        )


@dataclass
class DeviceCapability:
    type: str
    instance: str
    parameters: CapabilityParameter | None = None
    min_value: int | None = None
    max_value: int | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DeviceCapability:
        params_data = data.get("parameters", {})
        parameters = CapabilityParameter.from_api(params_data) if params_data else None

        # Extract range constraints
        min_value = None
        max_value = None
        if parameters and parameters.range:
            min_value = parameters.range.get("min")
            max_value = parameters.range.get("max")

        return cls(
            type=data.get("type", ""),
            instance=data.get("instance", ""),
            parameters=parameters,
            min_value=min_value,
            max_value=max_value,
        )
