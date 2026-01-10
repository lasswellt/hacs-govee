"""Test fixtures for Govee integration tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock

import pytest

from custom_components.govee.api import (
    GoveeApiClient,
    GoveeIotCredentials,
)
from custom_components.govee.models import (
    GoveeCapability,
    GoveeDevice,
    GoveeDeviceState,
    RGBColor,
)
from custom_components.govee.models.device import (
    CAPABILITY_COLOR_SETTING,
    CAPABILITY_DYNAMIC_SCENE,
    CAPABILITY_ON_OFF,
    CAPABILITY_RANGE,
    CAPABILITY_SEGMENT_COLOR,
    INSTANCE_BRIGHTNESS,
    INSTANCE_COLOR_RGB,
    INSTANCE_COLOR_TEMP,
    INSTANCE_POWER,
    INSTANCE_SCENE,
)

# Capability constants for test devices
DEVICE_TYPE_LIGHT = "devices.types.light"
DEVICE_TYPE_PLUG = "devices.types.socket"


@pytest.fixture
def mock_api_client() -> Generator[AsyncMock, None, None]:
    """Create a mock API client."""
    client = AsyncMock(spec=GoveeApiClient)
    client.rate_limit_remaining = 100
    client.rate_limit_total = 100
    client.rate_limit_reset = 0
    client.get_devices = AsyncMock(return_value=[])
    client.get_device_state = AsyncMock()
    client.control_device = AsyncMock(return_value=True)
    client.get_dynamic_scenes = AsyncMock(return_value=[])
    client.close = AsyncMock()
    yield client


@pytest.fixture
def mock_iot_credentials() -> GoveeIotCredentials:
    """Create mock IoT credentials."""
    return GoveeIotCredentials(
        token="test_token",
        refresh_token="test_refresh",
        account_topic="GA/test_account",
        iot_cert="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----",
        iot_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        iot_ca=None,
        client_id="AP/12345/testclient",
        endpoint="test.iot.amazonaws.com",
    )


@pytest.fixture
def light_capabilities() -> tuple[GoveeCapability, ...]:
    """Create capabilities for a typical light device."""
    return (
        GoveeCapability(
            type=CAPABILITY_ON_OFF,
            instance=INSTANCE_POWER,
            parameters={},
        ),
        GoveeCapability(
            type=CAPABILITY_RANGE,
            instance=INSTANCE_BRIGHTNESS,
            parameters={"range": {"min": 0, "max": 100}},
        ),
        GoveeCapability(
            type=CAPABILITY_COLOR_SETTING,
            instance=INSTANCE_COLOR_RGB,
            parameters={},
        ),
        GoveeCapability(
            type=CAPABILITY_COLOR_SETTING,
            instance=INSTANCE_COLOR_TEMP,
            parameters={"range": {"min": 2000, "max": 9000}},
        ),
        GoveeCapability(
            type=CAPABILITY_DYNAMIC_SCENE,
            instance=INSTANCE_SCENE,
            parameters={},
        ),
    )


@pytest.fixture
def rgbic_capabilities(light_capabilities) -> tuple[GoveeCapability, ...]:
    """Create capabilities for an RGBIC device."""
    return light_capabilities + (
        GoveeCapability(
            type=CAPABILITY_SEGMENT_COLOR,
            instance="segmentedColorRgb",
            parameters={"segmentCount": 15},
        ),
    )


@pytest.fixture
def plug_capabilities() -> tuple[GoveeCapability, ...]:
    """Create capabilities for a smart plug."""
    return (
        GoveeCapability(
            type=CAPABILITY_ON_OFF,
            instance=INSTANCE_POWER,
            parameters={},
        ),
    )


@pytest.fixture
def mock_light_device(light_capabilities) -> GoveeDevice:
    """Create a mock light device."""
    return GoveeDevice(
        device_id="AA:BB:CC:DD:EE:FF:00:11",
        sku="H6072",
        name="Living Room Light",
        device_type=DEVICE_TYPE_LIGHT,
        capabilities=light_capabilities,
        is_group=False,
    )


@pytest.fixture
def mock_rgbic_device(rgbic_capabilities) -> GoveeDevice:
    """Create a mock RGBIC LED strip device."""
    return GoveeDevice(
        device_id="AA:BB:CC:DD:EE:FF:00:22",
        sku="H6167",
        name="Bedroom LED Strip",
        device_type=DEVICE_TYPE_LIGHT,
        capabilities=rgbic_capabilities,
        is_group=False,
    )


@pytest.fixture
def mock_plug_device(plug_capabilities) -> GoveeDevice:
    """Create a mock smart plug device."""
    return GoveeDevice(
        device_id="AA:BB:CC:DD:EE:FF:00:33",
        sku="H5080",
        name="Office Plug",
        device_type=DEVICE_TYPE_PLUG,
        capabilities=plug_capabilities,
        is_group=False,
    )


@pytest.fixture
def mock_group_device(light_capabilities) -> GoveeDevice:
    """Create a mock group device."""
    return GoveeDevice(
        device_id="GROUP:AA:BB:CC:DD:EE:FF",
        sku="GROUP",
        name="All Lights",
        device_type="devices.types.group",
        capabilities=light_capabilities,
        is_group=True,
    )


@pytest.fixture
def mock_device_state() -> GoveeDeviceState:
    """Create a mock device state."""
    return GoveeDeviceState(
        device_id="AA:BB:CC:DD:EE:FF:00:11",
        online=True,
        power_state=True,
        brightness=75,
        color=RGBColor(r=255, g=128, b=64),
        color_temp_kelvin=None,
        active_scene=None,
        source="api",
    )


@pytest.fixture
def mock_device_state_off() -> GoveeDeviceState:
    """Create a mock device state (off)."""
    return GoveeDeviceState(
        device_id="AA:BB:CC:DD:EE:FF:00:11",
        online=True,
        power_state=False,
        brightness=0,
        color=None,
        color_temp_kelvin=None,
        active_scene=None,
        source="api",
    )


@pytest.fixture
def mock_scenes() -> list[dict[str, Any]]:
    """Create mock scene data."""
    return [
        {"name": "Sunrise", "value": {"id": 1}},
        {"name": "Sunset", "value": {"id": 2}},
        {"name": "Party", "value": {"id": 3}},
        {"name": "Movie", "value": {"id": 4}},
    ]


@pytest.fixture
def api_device_response() -> dict[str, Any]:
    """Create a mock API device response."""
    return {
        "device": "AA:BB:CC:DD:EE:FF:00:11",
        "sku": "H6072",
        "deviceName": "Living Room Light",
        "type": "devices.types.light",
        "capabilities": [
            {"type": CAPABILITY_ON_OFF, "instance": INSTANCE_POWER, "parameters": {}},
            {
                "type": CAPABILITY_RANGE,
                "instance": INSTANCE_BRIGHTNESS,
                "parameters": {"range": {"min": 0, "max": 100}},
            },
            {"type": CAPABILITY_COLOR_SETTING, "instance": INSTANCE_COLOR_RGB, "parameters": {}},
        ],
    }


@pytest.fixture
def api_state_response() -> dict[str, Any]:
    """Create a mock API state response."""
    return {
        "capabilities": [
            {
                "type": "devices.capabilities.online",
                "instance": "online",
                "state": {"value": True},
            },
            {
                "type": CAPABILITY_ON_OFF,
                "instance": INSTANCE_POWER,
                "state": {"value": 1},
            },
            {
                "type": CAPABILITY_RANGE,
                "instance": INSTANCE_BRIGHTNESS,
                "state": {"value": 75},
            },
            {
                "type": CAPABILITY_COLOR_SETTING,
                "instance": INSTANCE_COLOR_RGB,
                "state": {"value": 16744512},  # RGB(255, 128, 64)
            },
        ],
    }


@pytest.fixture
def mqtt_state_message() -> dict[str, Any]:
    """Create a mock MQTT state message."""
    return {
        "device": "AA:BB:CC:DD:EE:FF:00:11",
        "sku": "H6072",
        "state": {
            "onOff": 1,
            "brightness": 75,
            "color": {"r": 255, "g": 128, "b": 64},
            "colorTemInKelvin": 0,
        },
    }
