"""Test API type definitions.

This tests that TypedDict definitions are properly structured and can be used.
"""
from __future__ import annotations

import pytest

from custom_components.govee.api.requests import (
    DeviceIdentifier,
    DeviceStateRequestPayload,
    ControlRequestInnerPayload,
    ControlRequestPayload,
    SceneRequestPayload,
    OnOffValue,
    BrightnessValue,
    ColorRGBValue,
    ColorTempValue,
    SceneValue,
    SegmentColorValue,
    SegmentBrightnessValue,
    MusicModeValue,
)
from custom_components.govee.api.responses import (
    DeviceDict,
    DevicesResponsePayload,
    DeviceStatePayload,
    ControlResponsePayload,
    SceneCapabilityDict,
    DynamicScenesPayload,
    DIYScenesPayload,
    ApiResponseBase,
    DevicesResponse,
    DeviceStateResponse,
    ControlResponse,
    DynamicScenesResponse,
    DIYScenesResponse,
)
from custom_components.govee.api.types import (
    RangeDict,
    OptionDict,
    FieldDict,
    ParametersDict,
    CapabilityStateDict,
    StateCapabilityDict,
    DeviceCapabilityDict,
    SceneOptionDict,
    CapabilityCommandDict,
)


class TestApiRequestTypes:
    """Test API request TypedDicts."""

    def test_device_identifier(self):
        """Test DeviceIdentifier TypedDict."""
        identifier: DeviceIdentifier = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
        }
        assert identifier["sku"] == "H6160"
        assert identifier["device"] == "AA:BB:CC:DD:EE:FF:GG:HH"

    def test_device_state_request_payload(self):
        """Test DeviceStateRequestPayload TypedDict."""
        payload: DeviceStateRequestPayload = {
            "requestId": "test-request-id",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            },
        }
        assert payload["requestId"] == "test-request-id"
        assert payload["payload"]["sku"] == "H6160"

    def test_control_request_inner_payload(self):
        """Test ControlRequestInnerPayload TypedDict."""
        inner: ControlRequestInnerPayload = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "capability": {
                "type": "devices.capabilities.on_off",
                "instance": "powerSwitch",
                "value": 1,
            },
        }
        assert inner["sku"] == "H6160"
        assert inner["capability"]["type"] == "devices.capabilities.on_off"

    def test_control_request_payload(self):
        """Test ControlRequestPayload TypedDict."""
        payload: ControlRequestPayload = {
            "requestId": "test-request-id",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
                "capability": {
                    "type": "devices.capabilities.on_off",
                    "instance": "powerSwitch",
                    "value": 1,
                },
            },
        }
        assert payload["requestId"] == "test-request-id"

    def test_scene_request_payload(self):
        """Test SceneRequestPayload TypedDict."""
        payload: SceneRequestPayload = {
            "requestId": "test-request-id",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            },
        }
        assert payload["requestId"] == "test-request-id"

    def test_on_off_value(self):
        """Test OnOffValue TypedDict."""
        value: OnOffValue = {"value": 1}
        assert value["value"] == 1

    def test_brightness_value(self):
        """Test BrightnessValue TypedDict."""
        value: BrightnessValue = {"value": 100}
        assert value["value"] == 100

    def test_color_rgb_value(self):
        """Test ColorRGBValue TypedDict."""
        value: ColorRGBValue = {"value": {"r": 255, "g": 128, "b": 64}}
        assert value["value"]["r"] == 255

    def test_color_temp_value(self):
        """Test ColorTempValue TypedDict."""
        value: ColorTempValue = {"value": 4500}
        assert value["value"] == 4500

    def test_scene_value(self):
        """Test SceneValue TypedDict."""
        value: SceneValue = {"value": {"id": 1, "name": "Movie"}}
        assert value["value"]["id"] == 1

    def test_segment_color_value(self):
        """Test SegmentColorValue TypedDict."""
        value: SegmentColorValue = {
            "value": {
                "segment": [0, 1, 2],
                "rgb": 16711680,  # Red
            }
        }
        assert value["value"]["segment"] == [0, 1, 2]

    def test_segment_brightness_value(self):
        """Test SegmentBrightnessValue TypedDict."""
        value: SegmentBrightnessValue = {
            "value": {
                "segment": [0, 1],
                "brightness": 50,
            }
        }
        assert value["value"]["brightness"] == 50

    def test_music_mode_value(self):
        """Test MusicModeValue TypedDict."""
        value: MusicModeValue = {
            "value": {
                "musicMode": 1,
                "sensitivity": 80,
                "autoColor": 1,
            }
        }
        assert value["value"]["musicMode"] == 1


class TestApiResponseTypes:
    """Test API response TypedDicts."""

    def test_device_dict(self):
        """Test DeviceDict TypedDict."""
        device: DeviceDict = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "deviceName": "Living Room Light",
            "type": "devices.types.light",
            "capabilities": [],
        }
        assert device["deviceName"] == "Living Room Light"

    def test_devices_response_payload(self):
        """Test DevicesResponsePayload TypedDict."""
        payload: DevicesResponsePayload = {"data": []}
        assert payload["data"] == []

    def test_device_state_payload(self):
        """Test DeviceStatePayload TypedDict."""
        payload: DeviceStatePayload = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "capabilities": [],
        }
        assert payload["sku"] == "H6160"

    def test_control_response_payload(self):
        """Test ControlResponsePayload TypedDict."""
        payload: ControlResponsePayload = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "capability": {
                "type": "devices.capabilities.on_off",
                "instance": "powerSwitch",
                "value": 1,
            },
        }
        assert payload["sku"] == "H6160"

    def test_scene_capability_dict(self):
        """Test SceneCapabilityDict TypedDict."""
        scene: SceneCapabilityDict = {
            "name": "Movie",
            "value": {"id": 1, "name": "Movie"},
        }
        assert scene["name"] == "Movie"

    def test_dynamic_scenes_payload(self):
        """Test DynamicScenesPayload TypedDict."""
        payload: DynamicScenesPayload = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "capabilities": [],
        }
        assert payload["sku"] == "H6160"

    def test_diy_scenes_payload(self):
        """Test DIYScenesPayload TypedDict."""
        payload: DIYScenesPayload = {
            "sku": "H6160",
            "device": "AA:BB:CC:DD:EE:FF:GG:HH",
            "capabilities": [],
        }
        assert payload["sku"] == "H6160"

    def test_api_response_base(self):
        """Test ApiResponseBase TypedDict."""
        response: ApiResponseBase = {
            "code": 200,
            "message": "success",
        }
        assert response["code"] == 200

    def test_devices_response(self):
        """Test DevicesResponse TypedDict."""
        response: DevicesResponse = {
            "code": 200,
            "message": "success",
            "data": [],
        }
        assert response["code"] == 200

    def test_device_state_response(self):
        """Test DeviceStateResponse TypedDict."""
        response: DeviceStateResponse = {
            "code": 200,
            "message": "success",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
                "capabilities": [],
            },
        }
        assert response["code"] == 200

    def test_control_response(self):
        """Test ControlResponse TypedDict."""
        response: ControlResponse = {
            "code": 200,
            "message": "success",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
                "capability": {
                    "type": "devices.capabilities.on_off",
                    "instance": "powerSwitch",
                    "value": 1,
                },
            },
        }
        assert response["code"] == 200

    def test_dynamic_scenes_response(self):
        """Test DynamicScenesResponse TypedDict."""
        response: DynamicScenesResponse = {
            "code": 200,
            "message": "success",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
                "capabilities": [],
            },
        }
        assert response["code"] == 200

    def test_diy_scenes_response(self):
        """Test DIYScenesResponse TypedDict."""
        response: DIYScenesResponse = {
            "code": 200,
            "message": "success",
            "payload": {
                "sku": "H6160",
                "device": "AA:BB:CC:DD:EE:FF:GG:HH",
                "capabilities": [],
            },
        }
        assert response["code"] == 200


class TestApiGenericTypes:
    """Test generic API TypedDicts."""

    def test_range_dict(self):
        """Test RangeDict TypedDict."""
        range_dict: RangeDict = {"min": 0, "max": 100}
        assert range_dict["min"] == 0
        assert range_dict["max"] == 100

    def test_option_dict(self):
        """Test OptionDict TypedDict."""
        option: OptionDict = {"name": "Movie", "value": 1}
        assert option["name"] == "Movie"

    def test_field_dict(self):
        """Test FieldDict TypedDict."""
        field: FieldDict = {"fieldName": "color", "defaultValue": 0}
        assert field["fieldName"] == "color"

    def test_parameters_dict(self):
        """Test ParametersDict TypedDict."""
        params: ParametersDict = {"range": {"min": 0, "max": 100}}
        assert params["range"]["min"] == 0

    def test_capability_state_dict(self):
        """Test CapabilityStateDict TypedDict."""
        state: CapabilityStateDict = {"value": 1}
        assert state["value"] == 1

    def test_state_capability_dict(self):
        """Test StateCapabilityDict TypedDict."""
        cap: StateCapabilityDict = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "state": {"value": 1},
        }
        assert cap["instance"] == "powerSwitch"

    def test_device_capability_dict(self):
        """Test DeviceCapabilityDict TypedDict."""
        cap: DeviceCapabilityDict = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "parameters": {},
        }
        assert cap["type"] == "devices.capabilities.on_off"

    def test_scene_option_dict(self):
        """Test SceneOptionDict TypedDict."""
        scene: SceneOptionDict = {
            "name": "Movie",
            "value": {"id": 1, "name": "Movie"},
        }
        assert scene["name"] == "Movie"

    def test_capability_command_dict(self):
        """Test CapabilityCommandDict TypedDict."""
        cmd: CapabilityCommandDict = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 1,
        }
        assert cmd["value"] == 1
