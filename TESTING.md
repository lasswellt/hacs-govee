# Testing Guide

This document explains how to run tests, write new tests, and understand the testing infrastructure for the Govee integration.

---

## Quick Start

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run all tests with tox (recommended - includes linting)
tox

# Run tests with coverage
pytest --cov=custom_components.govee --cov-report=term-missing

# Run specific test file
pytest tests/test_light.py

# Run specific test
pytest tests/test_models.py::TestRGBColor::test_valid_color
```

---

## Test Infrastructure

### Dependencies

Required packages (from `requirements_test.txt`):

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage measurement |
| `pytest-homeassistant-custom-component` | HA test fixtures |
| `flake8` | Linting |
| `mypy` | Type checking |
| `black` | Code formatting |

### Configuration

**pytest.ini**:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = --cov=custom_components.govee --cov-fail-under=95
```

**tox.ini**:
```ini
[tox]
envlist = py312,py313

[testenv]
deps = -r{toxinidir}/requirements_test.txt
commands =
    flake8 .
    mypy custom_components/govee
    pytest --cov=custom_components.govee --cov-fail-under=95
```

---

## Test Organization

```
tests/
├── __init__.py              # Package init
├── conftest.py              # Shared fixtures
├── test_models.py           # Domain models (RGBColor, Device, State, Commands)
├── test_api_client.py       # API client and exceptions
├── test_coordinator.py      # Coordinator logic and observer pattern
└── test_config_flow.py      # Config flow, options, reauth, reconfigure, repairs
```

### Test Coverage by File

| File | Tests | Focus |
|------|-------|-------|
| `test_models.py` | 50 | RGBColor, GoveeDevice, GoveeDeviceState, Commands |
| `test_config_flow.py` | 41 | Config flow, options, reauth, reconfigure, repairs |
| `test_coordinator.py` | 32 | Observer pattern, commands, state management |
| `test_api_client.py` | 28 | Exceptions, client creation, rate limits |
| **Total** | **151** | |

---

## Running Tests

### Full Test Suite

```bash
# Using tox (runs linting + type checking + tests)
tox

# Using pytest directly
pytest

# Verbose output
pytest -v

# Show print statements
pytest -vv -s
```

### Specific Tests

```bash
# Single file
pytest tests/test_coordinator.py

# Single class
pytest tests/test_models.py::TestGoveeDevice

# Single test
pytest tests/test_config_flow.py::TestReconfigureFlow::test_reconfigure_success

# Pattern matching
pytest -k "test_turn_on"

# Only failed tests from last run
pytest --lf
```

### Coverage

```bash
# Terminal report with missing lines
pytest --cov=custom_components.govee --cov-report=term-missing

# HTML report
pytest --cov=custom_components.govee --cov-report=html
open htmlcov/index.html

# Fail if below threshold
pytest --cov=custom_components.govee --cov-fail-under=95
```

### Linting and Type Checking

```bash
# Linting
flake8 .

# Type checking
mypy custom_components/govee

# Code formatting
black --check .
```

---

## Writing Tests

### Test Structure

Use class-based organization with descriptive names:

```python
import pytest
from custom_components.govee.models import RGBColor

class TestRGBColor:
    """Tests for RGBColor dataclass."""

    def test_valid_color(self):
        """Test creating valid RGB color."""
        color = RGBColor(255, 128, 0)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0

    def test_invalid_color_raises(self):
        """Test invalid color values raise ValueError."""
        with pytest.raises(ValueError):
            RGBColor(256, 0, 0)
```

### Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation(mock_api_client):
    """Test async API call."""
    mock_api_client.get_devices = AsyncMock(return_value=[])

    result = await mock_api_client.get_devices()

    assert result == []
```

### Using Fixtures

Fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def mock_device_light():
    """Factory fixture for light devices."""
    def _create(device_id="test_id", device_name="Test Light"):
        return GoveeDevice(
            device_id=device_id,
            device_name=device_name,
            model="H6XXX",
            # ... other properties
        )
    return _create

# Usage
def test_device(mock_device_light):
    device = mock_device_light(device_id="custom_id")
    assert device.device_id == "custom_id"
```

### Mocking API Calls

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_api_error(mock_api_client):
    """Test API error handling."""
    mock_api_client.get_device_state = AsyncMock(
        side_effect=GoveeAuthError("Invalid key")
    )

    with pytest.raises(GoveeAuthError):
        await mock_api_client.get_device_state("device_1", "H6XXX")
```

---

## Coverage Requirements

| Component | Minimum |
|-----------|---------|
| Overall | 95% |
| Critical (coordinator, API) | 100% |
| Per-file | 90% |

### Excluded from Coverage

```python
# Lines excluded via pragma
if TYPE_CHECKING:  # pragma: no cover
    from homeassistant.core import HomeAssistant

def __repr__(self) -> str:  # pragma: no cover
    return f"Device({self.device_id})"
```

---

## CI/CD

### GitHub Actions

Tests run automatically on:
- Push to `master` or `develop`
- Pull requests

Workflow (`.github/workflows/tox.yaml`):
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install tox
      - run: tox
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Runs before each commit:
- Black (formatting)
- Flake8 (linting)
- Mypy (type checking)

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: homeassistant` | Run `pip install -r requirements_test.txt` |
| `await outside async function` | Add `@pytest.mark.asyncio` decorator |
| Mock not returning value | Use `AsyncMock` for async methods |
| Tests pass locally, fail in CI | Check Python version compatibility |

### Debug Commands

```bash
pytest -s           # Show print statements
pytest -x           # Stop on first failure
pytest -l           # Show locals on failure
pytest --pdb        # Drop into debugger
pytest -vv          # Extra verbosity
```

---

## Best Practices

### Do

- Use descriptive test names: `test_turn_on_with_brightness_and_color`
- Test one behavior per test
- Use fixtures for common setup
- Mock all external dependencies
- Test both success and error paths
- Keep tests fast

### Don't

- Make real API calls
- Share state between tests
- Skip tests for "simple" code
- Depend on test execution order
- Test Home Assistant internals

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
