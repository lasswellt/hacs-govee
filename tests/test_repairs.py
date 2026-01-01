"""Test Govee repairs module."""
from __future__ import annotations

import pytest

from custom_components.govee.repairs import (
    async_create_fix_flow,
    GoveeAuthRepairFlow,
)


class TestGoveeAuthRepairFlow:
    """Test GoveeAuthRepairFlow class."""

    @pytest.mark.asyncio
    async def test_repair_flow_init_step(self):
        """Test repair flow init step."""
        flow = GoveeAuthRepairFlow("entry_123")

        result = await flow.async_step_init(None)

        assert result["type"] == "create_entry"


class TestAsyncCreateFixFlow:
    """Test async_create_fix_flow function."""

    @pytest.mark.asyncio
    async def test_create_fix_flow_auth(self):
        """Test creating fix flow for auth issue."""
        flow = await async_create_fix_flow(
            None, "auth_failed_entry_123", {"entry_id": "entry_123"}
        )

        assert isinstance(flow, GoveeAuthRepairFlow)

    @pytest.mark.asyncio
    async def test_create_fix_flow_unknown(self):
        """Test creating fix flow for unknown issue raises error."""
        with pytest.raises(ValueError, match="Unknown issue_id"):
            await async_create_fix_flow(None, "unknown_issue", None)
