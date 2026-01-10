# CLAUDE.md

Instructions for Claude Code when working with this repository.

## Project Overview

**Govee Integration for Home Assistant** - A HACS custom component that controls Govee lights, LED strips, and smart devices via the Govee Cloud API v2.0.

| Attribute | Value |
|-----------|-------|
| Type | Home Assistant Custom Component |
| Language | Python 3.12+ |
| Integration Type | Hub (cloud service) |
| IoT Class | cloud_push (MQTT + polling) |
| API Version | Govee API v2.0 |

## Quick Commands

```bash
# Run tests (recommended)
tox

# Run pytest directly
pytest

# Single test file
pytest tests/test_config_flow.py

# Single test
pytest tests/test_models.py::TestRGBColor::test_valid_color

# Format code
black .

# Lint
flake8 .

# Type check
mypy custom_components/govee
```

## Directory Structure

```
custom_components/govee/
├── __init__.py          # Entry point, async_setup_entry
├── config_flow.py       # Config/options/reauth/reconfigure flows
├── coordinator.py       # DataUpdateCoordinator with MQTT
├── entity.py            # Base GoveeEntity class
├── light.py             # Light platform
├── scene.py             # Scene platform
├── switch.py            # Switch platform (plugs, night light)
├── sensor.py            # Diagnostic sensors
├── button.py            # Refresh scenes button
├── services.py          # Custom services
├── repairs.py           # Repairs framework integration
├── diagnostics.py       # Diagnostics for troubleshooting
├── const.py             # Constants
├── models/              # Domain models (frozen dataclasses)
│   ├── device.py        # GoveeDevice, GoveeCapability
│   ├── state.py         # GoveeDeviceState, RGBColor
│   └── commands.py      # Command pattern implementations
├── protocols/           # Protocol interfaces (Clean Architecture)
│   ├── api.py           # IApiClient, IAuthProvider
│   └── state.py         # IStateProvider, IStateObserver
└── api/                 # API layer
    ├── client.py        # GoveeApiClient (REST)
    ├── auth.py          # GoveeAuthClient (account login)
    ├── mqtt.py          # GoveeAwsIotClient (AWS IoT MQTT)
    └── exceptions.py    # Exception hierarchy
```

## Architecture Patterns

### Clean Architecture
- **Models**: Immutable frozen dataclasses, no I/O
- **Protocols**: Abstract interfaces (Python Protocols)
- **API Layer**: HTTP/MQTT clients, exception handling
- **Coordinator**: State management, orchestration
- **Entities**: Home Assistant platform integration

### Command Pattern
Device control uses immutable command objects:
```python
PowerCommand(device_id="xxx", value=True)
BrightnessCommand(device_id="xxx", value=128)
ColorCommand(device_id="xxx", value=RGBColor(255, 0, 0))
```

### Observer Pattern
Entities register as observers for state changes:
```python
coordinator.register_observer(device_id, entity)
```

## Key Components

### GoveeDataUpdateCoordinator
Central hub managing:
- Device discovery and state polling
- MQTT real-time updates
- Scene caching
- Optimistic state updates
- Repairs integration

### GoveeApiClient
REST client with:
- aiohttp-retry for resilience
- Rate limit tracking
- Parallel state fetching
- Command serialization

### GoveeAwsIotClient
MQTT client for real-time updates:
- AWS IoT Core connection
- Certificate-based auth
- State push notifications

## Testing

| File | Tests | Focus |
|------|-------|-------|
| test_models.py | 50 | RGBColor, Device, State, Commands |
| test_config_flow.py | 41 | Config, options, reauth, reconfigure |
| test_coordinator.py | 32 | Observer pattern, commands, state |
| test_api_client.py | 28 | Exceptions, client, rate limits |
| **Total** | **151** | |

## Code Style

- **Formatting**: Black (line length 119)
- **Linting**: Flake8
- **Types**: mypy strict mode
- **Docstrings**: Google style
- **Coverage**: 95% minimum

## Common Tasks

### Add a new platform
1. Create `platform.py` with entity class
2. Register in `__init__.py` PLATFORMS list
3. Add to coordinator device processing
4. Add tests

### Add a new command
1. Add command class to `models/commands.py`
2. Implement in `api/client.py`
3. Add coordinator method
4. Add entity method
5. Add tests

### Handle a new error type
1. Add exception to `api/exceptions.py`
2. Handle in coordinator
3. Consider repairs integration
4. Add tests

## Important Notes

- All I/O must be async
- Use `asyncio.gather()` for parallel operations
- Entities inherit from `GoveeEntity` base class
- Coordinator manages all state - entities are observers
- MQTT is optional - polling is the fallback
- Rate limits: 100/min, 10,000/day
