from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SceneOption:
    name: str
    value: Any
    category: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SceneOption:
        return cls(
            name=data.get("name", ""),
            value=data.get("value"),
            category=data.get("category"),
        )

    def to_command_value(self) -> Any:
        return self.value
