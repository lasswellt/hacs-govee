"""Tests for Govee integration diagnostics."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.govee.const import DOMAIN, CONF_POLL_INTERVAL
from custom_components.govee.diagnostics import async_get_config_entry_diagnostics
from custom_components.govee.models import (
    GoveeDevice,
    GoveeDeviceState,
    GoveeRuntimeData,
    DeviceCapability,
    CapabilityParameter,
)


@pytest.fixture
def mock_devices() -> dict[str, GoveeDevice]:
    """Create mock devices for diagnostics."""
    return {
        "device_1": GoveeDevice(
            device_id="AA:BB:CC:DD:EE:FF:11:22",
            sku="H6160",
            device_name="Bedroom Light",
            device_type="devices.types.light",
            capabilities=[
                DeviceCapability(
                    type="devices.capabilities.on_off",
                    instance="powerSwitch",
                ),
                DeviceCapability(
                    type="devices.capabilities.range",
                    instance="brightness",
                    parameters=CapabilityParameter(
                        data_type="INTEGER",
                        range={"min": 0, "max": 100},
                    ),
                    min_value=0,
                    max_value=100,
                ),
                DeviceCapability(
                    type="devices.capabilities.color_setting",
                    instance="colorRgb",
                    parameters=CapabilityParameter(
                        data_type="STRUCT",
                        fields=[
                            {"fieldName": "r", "range": {"min": 0, "max": 255}},
                            {"fieldName": "g", "range": {"min": 0, "max": 255}},
                            {"fieldName": "b", "range": {"min": 0, "max": 255}},
                        ],
                    ),
                ),
                DeviceCapability(
                    type="devices.capabilities.color_setting",
                    instance="colorTemperatureK",
                    parameters=CapabilityParameter(
                        data_type="INTEGER",
                        range={"min": 2000, "max": 9000},
                    ),
                    min_value=2000,
                    max_value=9000,
                ),
            ],
            firmware_version="1.02.03",
        ),
        "device_2": GoveeDevice(
            device_id="AA:BB:CC:DD:EE:FF:33:44",
            sku="H5080",
            device_name="Office Outlet",
            device_type="devices.types.socket",
            capabilities=[
                DeviceCapability(
                    type="devices.capabilities.on_off",
                    instance="powerSwitch",
                ),
            ],
            firmware_version="1.00.01",
        ),
    }


@pytest.fixture
def mock_coordinator(mock_devices: dict[str, GoveeDevice]) -> MagicMock:
    """Create a mock coordinator for diagnostics."""
    coordinator = MagicMock()
    coordinator.devices = mock_devices
    coordinator.last_update_success = True
    coordinator._scene_cache = {"scene1": [], "scene2": []}
    coordinator._diy_scene_cache = {"diy1": []}
    coordinator.rate_limit_remaining_minute = 95
    coordinator.rate_limit_remaining = 9800
    return coordinator


@pytest.fixture
def mock_runtime_data(mock_coordinator: MagicMock, mock_api_client: MagicMock) -> GoveeRuntimeData:
    """Create mock runtime data for config entry."""
    return GoveeRuntimeData(
        client=mock_api_client,
        coordinator=mock_coordinator,
        devices=mock_coordinator.devices,
    )


@pytest.fixture
def diagnostics_config_entry(mock_runtime_data: GoveeRuntimeData) -> MockConfigEntry:
    """Create a mock config entry for diagnostics tests."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Govee",
        data={
            CONF_API_KEY: "secret_api_key_12345",
        },
        options={
            CONF_POLL_INTERVAL: 60,
        },
        entry_id="test_diagnostics_entry",
        unique_id="govee_diagnostics",
    )
    entry.runtime_data = mock_runtime_data
    return entry


async def test_async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics returns expected structure."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    # Check top-level structure
    assert "entry" in result
    assert "devices" in result
    assert "coordinator" in result
    assert "rate_limits" in result


async def test_diagnostics_entry_info(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains config entry info."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    entry_info = result["entry"]
    assert entry_info["title"] == "Govee"
    assert CONF_POLL_INTERVAL in entry_info["options"]
    assert entry_info["options"][CONF_POLL_INTERVAL] == 60


async def test_diagnostics_api_key_redacted(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics redacts API key."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    entry_info = result["entry"]
    # API key should be redacted (either "**REDACTED**" or not present)
    if CONF_API_KEY in entry_info["data"]:
        assert entry_info["data"][CONF_API_KEY] == "**REDACTED**"


async def test_diagnostics_device_info(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains device information."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    devices = result["devices"]
    assert len(devices) == 2

    # Check first device (light)
    device1 = devices["device_1"]
    assert device1["sku"] == "H6160"
    assert device1["name"] == "Bedroom Light"
    assert device1["type"] == "devices.types.light"
    assert device1["firmware_version"] == "1.02.03"
    assert device1["capabilities_count"] == 4

    # Check second device (socket)
    device2 = devices["device_2"]
    assert device2["sku"] == "H5080"
    assert device2["name"] == "Office Outlet"
    assert device2["type"] == "devices.types.socket"


async def test_diagnostics_device_supports(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains device support flags."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    device1_supports = result["devices"]["device_1"]["supports"]
    assert device1_supports["on_off"] is True
    assert device1_supports["brightness"] is True
    assert device1_supports["color"] is True
    assert device1_supports["color_temp"] is True

    # Socket device should only support on/off
    device2_supports = result["devices"]["device_2"]["supports"]
    assert device2_supports["on_off"] is True
    assert device2_supports["brightness"] is False
    assert device2_supports["color"] is False


async def test_diagnostics_device_ranges(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains device capability ranges."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    device1_ranges = result["devices"]["device_1"]["ranges"]
    assert device1_ranges["brightness"] is not None
    assert device1_ranges["color_temp"] is not None


async def test_diagnostics_coordinator_info(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains coordinator status."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    coord_info = result["coordinator"]
    assert coord_info["last_update_success"] is True
    assert coord_info["device_count"] == 2
    assert coord_info["scene_cache_size"] == 2
    assert coord_info["diy_scene_cache_size"] == 1


async def test_diagnostics_rate_limits(
    hass: HomeAssistant,
    diagnostics_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics contains rate limit information."""
    result = await async_get_config_entry_diagnostics(hass, diagnostics_config_entry)

    rate_limits = result["rate_limits"]
    assert rate_limits["remaining_minute"] == 95
    assert rate_limits["remaining_day"] == 9800


async def test_diagnostics_empty_devices(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test diagnostics with no devices."""
    coordinator = MagicMock()
    coordinator.devices = {}
    coordinator.last_update_success = True
    coordinator._scene_cache = {}
    coordinator._diy_scene_cache = {}
    coordinator.rate_limit_remaining_minute = 100
    coordinator.rate_limit_remaining = 10000

    runtime_data = GoveeRuntimeData(
        client=mock_api_client,
        coordinator=coordinator,
        devices={},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Govee",
        data={CONF_API_KEY: "test_key"},
        options={},
        entry_id="empty_test",
    )
    entry.runtime_data = runtime_data

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["devices"] == {}
    assert result["coordinator"]["device_count"] == 0


async def test_diagnostics_failed_update(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
    mock_devices: dict[str, GoveeDevice],
) -> None:
    """Test diagnostics shows failed coordinator update."""
    coordinator = MagicMock()
    coordinator.devices = mock_devices
    coordinator.last_update_success = False
    coordinator._scene_cache = {}
    coordinator._diy_scene_cache = {}
    coordinator.rate_limit_remaining_minute = 0
    coordinator.rate_limit_remaining = 0

    runtime_data = GoveeRuntimeData(
        client=mock_api_client,
        coordinator=coordinator,
        devices=mock_devices,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Govee",
        data={CONF_API_KEY: "test_key"},
        options={},
        entry_id="failed_test",
    )
    entry.runtime_data = runtime_data

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["coordinator"]["last_update_success"] is False
    assert result["rate_limits"]["remaining_minute"] == 0
    assert result["rate_limits"]["remaining_day"] == 0
