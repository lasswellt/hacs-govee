"""Constants for Govee integration."""

from typing import Final

DOMAIN: Final = "govee"

# Config entry keys
CONF_API_KEY: Final = "api_key"
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"

# Options keys
CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_ENABLE_GROUPS: Final = "enable_groups"
CONF_ENABLE_SCENES: Final = "enable_scenes"
CONF_ENABLE_DIY_SCENES: Final = "enable_diy_scenes"
CONF_ENABLE_SEGMENTS: Final = "enable_segments"

# Defaults
DEFAULT_POLL_INTERVAL: Final = 60  # seconds
DEFAULT_ENABLE_GROUPS: Final = False
DEFAULT_ENABLE_SCENES: Final = True
DEFAULT_ENABLE_DIY_SCENES: Final = True
DEFAULT_ENABLE_SEGMENTS: Final = True

# Platforms to set up
PLATFORMS: Final = ["light", "scene"]

# Config entry version (fresh start)
CONFIG_VERSION: Final = 1
