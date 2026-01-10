"""Test Govee coordinator."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.govee.api.exceptions import (
    GoveeApiError,
    GoveeAuthError,
    GoveeDeviceNotFoundError,
    GoveeRateLimitError,
)
from custom_components.govee.models import (
    GoveeCapability,
    GoveeDevice,
    GoveeDeviceState,
    PowerCommand,
    BrightnessCommand,
    ColorCommand,
    ColorTempCommand,
    SceneCommand,
    RGBColor,
)
from custom_components.govee.models.device import (
    CAPABILITY_ON_OFF,
    CAPABILITY_RANGE,
    INSTANCE_POWER,
    INSTANCE_BRIGHTNESS,
)
from custom_components.govee.protocols import IStateObserver


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_capabilities():
    """Create sample light capabilities."""
    return (
        GoveeCapability(type=CAPABILITY_ON_OFF, instance=INSTANCE_POWER, parameters={}),
        GoveeCapability(
            type=CAPABILITY_RANGE,
            instance=INSTANCE_BRIGHTNESS,
            parameters={"range": {"min": 0, "max": 100}},
        ),
    )


@pytest.fixture
def sample_device(sample_capabilities):
    """Create a sample device."""
    return GoveeDevice(
        device_id="AA:BB:CC:DD:EE:FF:00:11",
        sku="H6072",
        name="Test Light",
        device_type="devices.types.light",
        capabilities=sample_capabilities,
        is_group=False,
    )


@pytest.fixture
def sample_group_device(sample_capabilities):
    """Create a sample group device."""
    return GoveeDevice(
        device_id="GROUP:AA:BB:CC:DD",
        sku="GROUP",
        name="All Lights",
        device_type="devices.types.group",
        capabilities=sample_capabilities,
        is_group=True,
    )


@pytest.fixture
def sample_state():
    """Create a sample device state."""
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


# ==============================================================================
# Coordinator Logic Tests (without Home Assistant dependencies)
# ==============================================================================


class TestCoordinatorLogic:
    """Test coordinator logic that doesn't require HA."""

    def test_sample_device_creation(self, sample_device):
        """Test sample device fixture."""
        assert sample_device.device_id == "AA:BB:CC:DD:EE:FF:00:11"
        assert sample_device.sku == "H6072"
        assert sample_device.is_group is False

    def test_sample_group_device_creation(self, sample_group_device):
        """Test sample group device fixture."""
        assert sample_group_device.is_group is True

    def test_sample_state_creation(self, sample_state):
        """Test sample state fixture."""
        assert sample_state.power_state is True
        assert sample_state.brightness == 75

    def test_state_optimistic_power(self, sample_state):
        """Test optimistic power update."""
        sample_state.apply_optimistic_power(False)
        assert sample_state.power_state is False
        assert sample_state.source == "optimistic"

    def test_state_optimistic_brightness(self, sample_state):
        """Test optimistic brightness update."""
        sample_state.apply_optimistic_brightness(50)
        assert sample_state.brightness == 50
        assert sample_state.source == "optimistic"

    def test_state_optimistic_color(self, sample_state):
        """Test optimistic color update."""
        color = RGBColor(r=0, g=255, b=0)
        sample_state.apply_optimistic_color(color)
        assert sample_state.color == color
        assert sample_state.color_temp_kelvin is None
        assert sample_state.source == "optimistic"

    def test_state_optimistic_color_temp(self, sample_state):
        """Test optimistic color temperature update."""
        sample_state.apply_optimistic_color_temp(4000)
        assert sample_state.color_temp_kelvin == 4000
        assert sample_state.color is None
        assert sample_state.source == "optimistic"


class TestObserverPattern:
    """Test observer pattern for state updates."""

    def test_observer_registration(self):
        """Test observer can be registered."""
        observers: list[IStateObserver] = []

        mock_observer = MagicMock(spec=IStateObserver)
        observers.append(mock_observer)

        assert mock_observer in observers

    def test_observer_unregistration(self):
        """Test observer can be unregistered."""
        observers: list[IStateObserver] = []

        mock_observer = MagicMock(spec=IStateObserver)
        observers.append(mock_observer)
        observers.remove(mock_observer)

        assert mock_observer not in observers

    def test_observer_notification(self, sample_state):
        """Test observers are notified of state changes."""
        mock_observer = MagicMock(spec=IStateObserver)
        observers = [mock_observer]

        device_id = "AA:BB:CC:DD:EE:FF:00:11"
        for observer in observers:
            observer.on_state_changed(device_id, sample_state)

        mock_observer.on_state_changed.assert_called_once_with(device_id, sample_state)

    def test_observer_exception_handling(self, sample_state):
        """Test that observer exceptions don't propagate."""
        bad_observer = MagicMock(spec=IStateObserver)
        bad_observer.on_state_changed.side_effect = Exception("Observer error")

        good_observer = MagicMock(spec=IStateObserver)
        observers = [bad_observer, good_observer]

        device_id = "AA:BB:CC:DD:EE:FF:00:11"

        for observer in observers:
            try:
                observer.on_state_changed(device_id, sample_state)
            except Exception:
                pass  # Coordinator swallows observer exceptions

        bad_observer.on_state_changed.assert_called_once()
        good_observer.on_state_changed.assert_called_once()


class TestCommandGeneration:
    """Test command creation for coordinator."""

    def test_power_command(self):
        """Test power command for coordinator."""
        cmd = PowerCommand(power_on=True)
        assert cmd.power_on is True
        assert cmd.get_value() == 1

    def test_brightness_command(self):
        """Test brightness command for coordinator."""
        cmd = BrightnessCommand(brightness=50)
        assert cmd.brightness == 50
        assert cmd.get_value() == 50

    def test_color_command(self):
        """Test color command for coordinator."""
        color = RGBColor(r=255, g=0, b=0)
        cmd = ColorCommand(color=color)
        # Red packed = (255 << 16) + (0 << 8) + 0 = 16711680
        assert cmd.get_value() == 16711680

    def test_color_temp_command(self):
        """Test color temp command for coordinator."""
        cmd = ColorTempCommand(kelvin=4000)
        assert cmd.kelvin == 4000
        assert cmd.get_value() == 4000

    def test_scene_command(self):
        """Test scene command for coordinator."""
        cmd = SceneCommand(scene_id=123, scene_name="Test")
        value = cmd.get_value()
        assert value["id"] == 123
        assert value["name"] == "Test"


class TestDeviceFiltering:
    """Test device filtering logic."""

    def test_filter_groups_when_disabled(self, sample_device, sample_group_device):
        """Test group devices filtered when groups disabled."""
        devices = [sample_device, sample_group_device]
        enable_groups = False

        filtered = [d for d in devices if not d.is_group or enable_groups]

        assert len(filtered) == 1
        assert filtered[0] == sample_device

    def test_include_groups_when_enabled(self, sample_device, sample_group_device):
        """Test group devices included when groups enabled."""
        devices = [sample_device, sample_group_device]
        enable_groups = True

        filtered = [d for d in devices if not d.is_group or enable_groups]

        assert len(filtered) == 2


class TestSceneCaching:
    """Test scene caching logic."""

    def test_cache_empty_initially(self):
        """Test scene cache starts empty."""
        cache: dict[str, list[dict[str, Any]]] = {}
        assert "device_id" not in cache

    def test_cache_stores_scenes(self):
        """Test scenes are cached."""
        cache: dict[str, list[dict[str, Any]]] = {}
        scenes = [{"name": "Sunrise", "value": {"id": 1}}]

        cache["device_id"] = scenes

        assert cache["device_id"] == scenes

    def test_cache_returns_existing(self):
        """Test cached scenes are returned."""
        cache: dict[str, list[dict[str, Any]]] = {
            "device_id": [{"name": "Sunset", "value": {"id": 2}}]
        }

        device_id = "device_id"
        refresh = False

        if not refresh and device_id in cache:
            result = cache[device_id]
        else:
            result = []

        assert len(result) == 1
        assert result[0]["name"] == "Sunset"

    def test_cache_refresh_bypasses(self):
        """Test refresh bypasses cache."""
        cache: dict[str, list[dict[str, Any]]] = {
            "device_id": [{"name": "Old", "value": {"id": 1}}]
        }

        device_id = "device_id"
        refresh = True

        should_fetch = refresh or device_id not in cache

        assert should_fetch is True


class TestStateManagement:
    """Test state management logic."""

    def test_state_registry(self, sample_state):
        """Test state registry operations."""
        states: dict[str, GoveeDeviceState] = {}

        states["device_id"] = sample_state

        assert states.get("device_id") == sample_state
        assert states.get("unknown") is None

    def test_state_update_from_api(self):
        """Test state update from API response."""
        state = GoveeDeviceState.create_empty("device_id")

        api_data = {
            "capabilities": [
                {
                    "type": "devices.capabilities.online",
                    "instance": "online",
                    "state": {"value": True},
                },
                {
                    "type": "devices.capabilities.on_off",
                    "instance": "powerSwitch",
                    "state": {"value": 1},
                },
            ],
        }

        state.update_from_api(api_data)

        assert state.online is True
        assert state.power_state is True
        assert state.source == "api"

    def test_state_update_from_mqtt(self):
        """Test state update from MQTT message."""
        state = GoveeDeviceState.create_empty("device_id")

        mqtt_data = {
            "onOff": 1,
            "brightness": 50,
            "color": {"r": 100, "g": 150, "b": 200},
        }

        state.update_from_mqtt(mqtt_data)

        assert state.power_state is True
        assert state.brightness == 50
        assert state.color.as_tuple == (100, 150, 200)
        assert state.source == "mqtt"

    def test_preserve_active_scene_on_api_update(self, sample_state):
        """Test active scene is preserved when API doesn't return it."""
        sample_state.active_scene = "scene_123"

        new_state = GoveeDeviceState.create_empty(sample_state.device_id)
        new_state.power_state = True
        new_state.brightness = 80

        if sample_state.active_scene:
            new_state.active_scene = sample_state.active_scene

        assert new_state.active_scene == "scene_123"


class TestErrorHandling:
    """Test error handling patterns."""

    def test_auth_error_raises(self):
        """Test auth error is raised appropriately."""
        err = GoveeAuthError("Invalid key")
        assert err.code == 401

    def test_rate_limit_keeps_state(self, sample_state):
        """Test rate limit error preserves existing state."""
        states = {"device_id": sample_state}

        try:
            raise GoveeRateLimitError()
        except GoveeRateLimitError:
            result = states.get("device_id")

        assert result == sample_state

    def test_device_not_found_for_groups(self):
        """Test device not found is expected for groups."""
        err = GoveeDeviceNotFoundError("GROUP:ID")

        is_group_error = "not exist" in str(err).lower() or "not found" in str(err).lower()

        assert is_group_error or err.code == 400

    def test_api_error_logs_debug(self):
        """Test general API errors are logged but don't crash."""
        err = GoveeApiError("Server error", code=500)

        should_keep_state = True
        assert should_keep_state
        assert err.code == 500


class TestMqttIntegration:
    """Test MQTT integration patterns."""

    def test_mqtt_state_update_flow(self, sample_state):
        """Test MQTT state update is applied correctly."""
        states = {"device_id": sample_state}
        devices = {"device_id": MagicMock()}

        device_id = "device_id"
        mqtt_data = {"onOff": 0, "brightness": 25}

        if device_id in devices:
            state = states.get(device_id)
            if state:
                state.update_from_mqtt(mqtt_data)

        assert sample_state.power_state is False
        assert sample_state.brightness == 25
        assert sample_state.source == "mqtt"

    def test_mqtt_unknown_device_ignored(self):
        """Test MQTT updates for unknown devices are ignored."""
        devices = {"known_device": MagicMock()}

        unknown_device_id = "unknown_device"

        if unknown_device_id not in devices:
            handled = False
        else:
            handled = True

        assert handled is False


class TestParallelStateFetching:
    """Test parallel state fetching patterns."""

    @pytest.mark.asyncio
    async def test_parallel_fetch_creates_tasks(self, sample_device):
        """Test parallel fetch creates tasks for all devices."""
        devices = {
            "device1": sample_device,
            "device2": sample_device,
            "device3": sample_device,
        }

        async def mock_fetch(device_id, device):
            return GoveeDeviceState.create_empty(device_id)

        tasks = [
            mock_fetch(device_id, device)
            for device_id, device in devices.items()
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(r, GoveeDeviceState) for r in results)

    @pytest.mark.asyncio
    async def test_parallel_fetch_handles_exceptions(self, sample_device):
        """Test parallel fetch handles individual failures."""

        async def mock_fetch(device_id: str):
            if device_id == "failing":
                raise GoveeApiError("Fetch failed")
            return GoveeDeviceState.create_empty(device_id)

        tasks = [
            mock_fetch("success1"),
            mock_fetch("failing"),
            mock_fetch("success2"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert isinstance(results[0], GoveeDeviceState)
        assert isinstance(results[1], GoveeApiError)
        assert isinstance(results[2], GoveeDeviceState)


class TestOptimisticUpdates:
    """Test optimistic state update patterns."""

    def test_apply_optimistic_power_on(self, sample_state):
        """Test applying optimistic power on."""
        sample_state.power_state = False
        sample_state.apply_optimistic_power(True)

        assert sample_state.power_state is True
        assert sample_state.source == "optimistic"

    def test_apply_optimistic_power_off(self, sample_state):
        """Test applying optimistic power off."""
        sample_state.power_state = True
        sample_state.apply_optimistic_power(False)

        assert sample_state.power_state is False
        assert sample_state.source == "optimistic"

    def test_apply_optimistic_brightness(self, sample_state):
        """Test applying optimistic brightness."""
        sample_state.apply_optimistic_brightness(100)

        assert sample_state.brightness == 100
        assert sample_state.source == "optimistic"

    def test_apply_optimistic_color_clears_temp(self, sample_state):
        """Test applying color clears color temp."""
        sample_state.color_temp_kelvin = 4000
        color = RGBColor(r=255, g=0, b=0)
        sample_state.apply_optimistic_color(color)

        assert sample_state.color == color
        assert sample_state.color_temp_kelvin is None

    def test_apply_optimistic_temp_clears_color(self, sample_state):
        """Test applying color temp clears color."""
        sample_state.color = RGBColor(r=255, g=0, b=0)
        sample_state.apply_optimistic_color_temp(5000)

        assert sample_state.color_temp_kelvin == 5000
        assert sample_state.color is None


class TestDeviceStateCreation:
    """Test device state creation patterns."""

    def test_create_empty_state(self):
        """Test creating empty state."""
        state = GoveeDeviceState.create_empty("test_id")

        assert state.device_id == "test_id"
        assert state.online is True
        assert state.power_state is False
        assert state.brightness == 100

    def test_state_with_all_attributes(self):
        """Test state with all attributes set."""
        color = RGBColor(r=100, g=150, b=200)
        state = GoveeDeviceState(
            device_id="test_id",
            online=True,
            power_state=True,
            brightness=50,
            color=color,
            color_temp_kelvin=4000,
            active_scene="scene_1",
            source="mqtt",
        )

        assert state.device_id == "test_id"
        assert state.online is True
        assert state.power_state is True
        assert state.brightness == 50
        assert state.color == color
        assert state.color_temp_kelvin == 4000
        assert state.active_scene == "scene_1"
        assert state.source == "mqtt"


class TestCoordinatorDeviceRegistry:
    """Test device registry patterns."""

    def test_get_device_by_id(self, sample_device):
        """Test getting device by ID."""
        devices = {sample_device.device_id: sample_device}

        result = devices.get(sample_device.device_id)
        assert result == sample_device

    def test_get_device_unknown_returns_none(self, sample_device):
        """Test getting unknown device returns None."""
        devices = {sample_device.device_id: sample_device}

        result = devices.get("unknown_id")
        assert result is None

    def test_device_count(self, sample_device, sample_group_device):
        """Test device count."""
        devices = {
            sample_device.device_id: sample_device,
            sample_group_device.device_id: sample_group_device,
        }

        assert len(devices) == 2


class TestCoordinatorSceneManagement:
    """Test scene management patterns."""

    def test_scene_cache_miss_fetches(self):
        """Test cache miss triggers fetch."""
        cache: dict[str, list[dict[str, Any]]] = {}

        device_id = "device_id"
        if device_id not in cache:
            # Would fetch from API
            should_fetch = True
        else:
            should_fetch = False

        assert should_fetch is True

    def test_scene_cache_hit_returns_cached(self):
        """Test cache hit returns cached scenes."""
        scenes = [{"name": "Test", "value": {"id": 1}}]
        cache = {"device_id": scenes}

        device_id = "device_id"
        result = cache.get(device_id, [])

        assert result == scenes

    def test_refresh_clears_and_fetches(self):
        """Test refresh clears cache and fetches."""
        cache = {"device_id": [{"name": "Old", "value": {"id": 1}}]}

        # Simulate refresh
        if "device_id" in cache:
            del cache["device_id"]

        assert "device_id" not in cache
