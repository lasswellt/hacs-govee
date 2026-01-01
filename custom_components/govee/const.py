from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "govee"

CONF_DISABLE_ATTRIBUTE_UPDATES = "disable_attribute_updates"
CONF_ENABLE_GROUP_DEVICES = "enable_group_devices"
CONF_OFFLINE_IS_OFF = "offline_is_off"
CONF_POLL_INTERVAL = "delay"
CONF_USE_ASSUMED_STATE = "use_assumed_state"

HA_BRIGHTNESS_MAX = 255
API_BRIGHTNESS_MAX = 100

COLOR_TEMP_KELVIN_MIN = 2000
COLOR_TEMP_KELVIN_MAX = 9000

DEFAULT_POLL_INTERVAL = 30

DEVICE_TYPE_LIGHT = "devices.types.light"
DEVICE_TYPE_SOCKET = "devices.types.socket"
DEVICE_TYPE_AIR_PURIFIER = "devices.types.air_purifier"
DEVICE_TYPE_HUMIDIFIER = "devices.types.humidifier"
DEVICE_TYPE_DEHUMIDIFIER = "devices.types.dehumidifier"
DEVICE_TYPE_HEATER = "devices.types.heater"
DEVICE_TYPE_THERMOMETER = "devices.types.thermometer"
DEVICE_TYPE_SENSOR = "devices.types.sensor"
DEVICE_TYPE_AROMA_DIFFUSER = "devices.types.aroma_diffuser"

UNSUPPORTED_DEVICE_SKUS = {"SameModeGroup", "BaseGroup", "DreamViewScenic"}

DEVICE_TYPE_PLATFORMS: dict[str, list[Platform]] = {
    DEVICE_TYPE_LIGHT: [Platform.LIGHT, Platform.SELECT],
    DEVICE_TYPE_SOCKET: [Platform.SWITCH],
    DEVICE_TYPE_AIR_PURIFIER: [Platform.FAN, Platform.SENSOR],
    DEVICE_TYPE_HUMIDIFIER: [Platform.HUMIDIFIER, Platform.SENSOR],
    DEVICE_TYPE_DEHUMIDIFIER: [Platform.HUMIDIFIER, Platform.SENSOR],
    DEVICE_TYPE_HEATER: [Platform.CLIMATE],
    DEVICE_TYPE_THERMOMETER: [Platform.SENSOR],
    DEVICE_TYPE_SENSOR: [Platform.SENSOR, Platform.BINARY_SENSOR],
    DEVICE_TYPE_AROMA_DIFFUSER: [Platform.FAN, Platform.SELECT],
}

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_ENTRY_VERSION = 2
