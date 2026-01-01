"""Repair flows for Govee integration."""
from __future__ import annotations

from typing import Any

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow


class GoveeAuthRepairFlow(RepairsFlow):
    """Handler for authentication repair flow."""

    def __init__(self, entry_id: str) -> None:
        """Initialize the repair flow."""
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the initial step - redirect to reconfigure."""
        return self.async_create_entry(data={})


async def async_create_fix_flow(
    hass: object,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """Create repair flow for fixable issues."""
    if issue_id.startswith("auth_failed_"):
        entry_id = data.get("entry_id", "") if data else ""
        return GoveeAuthRepairFlow(entry_id)
    raise ValueError(f"Unknown issue_id: {issue_id}")
