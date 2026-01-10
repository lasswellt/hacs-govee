# Govee Integration Architecture

This document provides a comprehensive overview of the Govee Home Assistant integration architecture.

---

## Overview

The Govee integration is a **hub-type** Home Assistant integration that connects to the Govee Cloud API v2.0 to control lights, LED strips, and smart plugs. It follows Clean Architecture principles with:

- **Config Flow**: UI-based configuration with reauth and reconfigure support
- **DataUpdateCoordinator**: Centralized state management and polling
- **Platform Entities**: Light, Scene, Switch, Sensor, Button platforms
- **Command Pattern**: Immutable command objects for device control
- **Protocol Interfaces**: Clean separation between layers
- **Repairs Framework**: Actionable notifications for common issues

**Integration Type**: `hub` (cloud service managing multiple devices)
**IoT Class**: `cloud_push` (MQTT real-time updates with polling fallback)
**API Version**: Govee API v2.0

---

## Directory Structure

```
custom_components/govee/
├── __init__.py              # Integration entry point
├── config_flow.py           # Config flow (user, account, reauth, reconfigure)
├── coordinator.py           # DataUpdateCoordinator with MQTT integration
├── entity.py                # Base entity class (GoveeEntity)
├── light.py                 # Light platform
├── scene.py                 # Scene platform
├── switch.py                # Switch platform (plugs, night light)
├── sensor.py                # Sensor platform (rate limit, MQTT status)
├── button.py                # Button platform (refresh scenes)
├── services.py              # Custom services
├── repairs.py               # Repairs framework integration
├── diagnostics.py           # Diagnostics for troubleshooting
├── const.py                 # Constants
├── manifest.json            # Integration metadata
├── strings.json             # UI strings
├── services.yaml            # Service definitions
├── quality_scale.yaml       # Quality scale tracking
├── translations/
│   └── en.json              # English translations
├── models/                  # Domain models (frozen dataclasses)
│   ├── __init__.py
│   ├── device.py            # GoveeDevice, GoveeCapability
│   ├── state.py             # GoveeDeviceState, RGBColor
│   └── commands.py          # Command pattern implementations
├── platforms/
│   ├── __init__.py
│   └── segment.py           # Segment light entities (RGBIC)
├── protocols/               # Protocol interfaces
│   ├── __init__.py
│   ├── api.py               # IApiClient, IAuthProvider
│   └── state.py             # IStateProvider, IStateObserver
└── api/                     # API layer
    ├── __init__.py
    ├── client.py            # GoveeApiClient (REST)
    ├── auth.py              # GoveeAuthClient (account login)
    ├── mqtt.py              # GoveeAwsIotClient (real-time MQTT)
    └── exceptions.py        # Exception hierarchy
```

---

## Component Responsibilities

### Entry Point (`__init__.py`)

- `async_setup_entry()`: Initialize integration
- `async_unload_entry()`: Clean up on removal
- Creates API client and coordinator
- Forwards platform setup
- Registers update listener for options changes

### Coordinator (`coordinator.py`)

Central hub for device state management:

- **Device Discovery**: Fetches devices from API on setup
- **Parallel State Fetching**: Queries all device states concurrently
- **MQTT Integration**: Real-time state updates via AWS IoT
- **Scene Caching**: Caches scenes to minimize API calls
- **Optimistic Updates**: Immediate UI feedback after commands
- **Observer Pattern**: Notifies entities of state changes
- **Repairs Integration**: Creates repair issues for errors

### Config Flow (`config_flow.py`)

UI-based configuration:

1. **User Step**: Enter API key
2. **Account Step**: Optional email/password for MQTT
3. **Reauth Step**: Re-authenticate on 401 errors
4. **Reconfigure Step**: Update credentials without removing integration
5. **Options Flow**: Poll interval, enable groups/scenes/segments

### Models (`models/`)

Frozen dataclasses for immutability:

- **GoveeDevice**: Device metadata and capabilities
- **GoveeDeviceState**: Current device state (mutable for updates)
- **RGBColor**: Immutable RGB color value
- **Commands**: PowerCommand, BrightnessCommand, ColorCommand, etc.

### Protocols (`protocols/`)

Clean Architecture interfaces:

- **IApiClient**: Contract for API operations
- **IAuthProvider**: Contract for authentication
- **IStateProvider**: Contract for state access
- **IStateObserver**: Contract for state change notifications

### API Layer (`api/`)

- **GoveeApiClient**: REST API with aiohttp-retry for resilience
- **GoveeAuthClient**: Account login and IoT credential retrieval
- **GoveeAwsIotClient**: AWS IoT MQTT for real-time updates
- **Exceptions**: Hierarchical exception classes with translation support

---

## Data Flow

### State Update Flow

```
Poll Interval Timer
        ↓
coordinator._async_update_data()
        ↓
Parallel: fetch state for all devices
        ↓
Process results:
  - Success → Update state
  - Auth Error → Create repair issue, trigger reauth
  - Rate Limit → Create repair issue, keep previous state
        ↓
coordinator.async_set_updated_data()
        ↓
Entities receive state update
```

### MQTT Real-time Flow

```
MQTT Message Received
        ↓
_on_mqtt_state_update()
        ↓
Update state from MQTT data
        ↓
coordinator.async_set_updated_data()
        ↓
Notify observers
        ↓
UI updated immediately
```

### Control Command Flow

```
User Action (turn on, set color, etc.)
        ↓
Entity method (async_turn_on, etc.)
        ↓
coordinator.async_control_device()
        ↓
Create Command object (immutable)
        ↓
API client sends command
        ↓
Apply optimistic state update
        ↓
UI updated immediately
```

---

## Platforms

| Platform | Entity Types | Description |
|----------|--------------|-------------|
| `light` | GoveeLightEntity, GoveeSegmentLight | Main lights and RGBIC segments |
| `scene` | GoveeSceneEntity | Dynamic scenes from Govee cloud |
| `switch` | GoveePlugSwitchEntity, GoveeNightLightSwitchEntity | Smart plugs, night light toggle |
| `sensor` | Rate limit, MQTT status | Diagnostic sensors |
| `button` | Refresh scenes | Manual scene refresh |

---

## Services

| Service | Description |
|---------|-------------|
| `govee.refresh_scenes` | Refresh scene list from API |
| `govee.set_segment_color` | Set color for RGBIC segments |

---

## Error Handling

### Exception Hierarchy

```
GoveeApiError (base)
├── GoveeAuthError (401) → Triggers reauth, creates repair issue
├── GoveeRateLimitError (429) → Creates repair issue, keeps previous state
├── GoveeConnectionError → Logs warning, retries
└── GoveeDeviceNotFoundError (400) → Expected for groups, uses optimistic state
```

### Repairs Framework

Actionable repair notifications:

- **auth_failed**: Fixable, guides to reauth flow
- **rate_limited**: Warning with reset time estimate
- **mqtt_disconnected**: Warning about real-time updates

---

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `poll_interval` | 60s | State refresh frequency |
| `enable_groups` | false | Include Govee app groups |
| `enable_scenes` | true | Create scene entities |
| `enable_segments` | true | Create segment entities for RGBIC |

---

## Quality Scale

The integration targets **Gold tier** compliance:

- ✅ Config flow with test coverage
- ✅ Unique entity IDs
- ✅ Device info for all entities
- ✅ Diagnostics platform
- ✅ Reauthentication flow
- ✅ Reconfigure flow
- ✅ Repairs framework
- ✅ Entity translations
- ✅ Async dependencies

See `quality_scale.yaml` for detailed compliance tracking.
